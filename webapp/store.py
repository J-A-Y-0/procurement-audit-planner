"""Single-process, persistent run records with atomic writes and version checks."""
import json
import io
import os
import re
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

class Conflict(ValueError):
    pass

class RunStore:
    def __init__(self, root, max_runs=100, persistence=None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.max_runs = max_runs
        self.persistence = persistence
        if persistence:
            for rid, record, archive in persistence.runs():
                folder = self.folder(rid)
                folder.mkdir(exist_ok=True)
                if archive:
                    with zipfile.ZipFile(io.BytesIO(archive)) as z:
                        for entry in z.infolist():
                            target = (folder / entry.filename).resolve()
                            if not target.is_relative_to(folder) or entry.filename == 'run.json':
                                raise ValueError('Invalid stored run archive.')
                        z.extractall(folder)
                (folder / 'run.json').write_bytes(record)

    def folder(self, rid):
        if not re.fullmatch(r'[0-9a-f]{32}', rid):
            raise KeyError(rid)
        return self.root / rid

    def _read(self, rid):
        try:
            return json.loads((self.folder(rid) / 'run.json').read_text())
        except (OSError, ValueError, KeyError):
            return None

    def _write(self, run):
        if self.persistence:
            archive = None
            if run['status'] not in ('queued', 'analysing', 'planning'):
                buffer = io.BytesIO()
                folder = self.folder(run['id'])
                with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
                    for p in sorted(folder.rglob('*')):
                        if p.is_file() and not p.is_symlink() and p.name not in ('run.json', 'run.tmp'):
                            z.write(p, p.relative_to(folder).as_posix())
                archive = buffer.getvalue()
            # Commit before acknowledging a gate or sign-off. Database failure
            # blocks the request; it never falls back to a resettable local ledger.
            self.persistence.save_run(run['id'], json.dumps(run).encode(), archive)
        path = self.folder(run['id']) / 'run.json'
        tmp = path.with_suffix('.tmp')
        with tmp.open('w') as f:
            json.dump(run, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)

    def get(self, rid, owner):
        with self.lock:
            run = self._read(rid)
            return run if run and run['owner'] == owner else None

    def list(self, owner):
        with self.lock:
            runs = [self._read(p.name) for p in self.root.iterdir() if p.is_dir()]
            return sorted([r for r in runs if r and r['owner'] == owner], key=lambda r:r['created_at'], reverse=True)

    def create(self, owner, title, mode):
        with self.lock:
            if len(list(self.root.glob('*/run.json'))) >= self.max_runs:
                raise Conflict('Run storage is full. Ask the operator to archive old runs.')
            if any(r['status'] in ('queued','analysing','planning') for r in self.list(owner)):
                raise Conflict('Wait for your current run to finish processing.')
            rid=uuid.uuid4().hex
            self.folder(rid).mkdir()
            at=now()
            run=dict(id=rid,owner=owner,title=title,mode=mode,status='queued',version=1,
                     created_at=at,updated_at=at,events=[{'label':'Run created','at':at}],
                     error=None,risks=[],decisions=None,qa=[],figures={},dataset_summary={},signoff=None)
            self._write(run)
            return run

    def change(self, rid, owner, expected, changes, allowed=None, event=None):
        with self.lock:
            run=self.get(rid,owner)
            if not run:
                raise KeyError(rid)
            if run['version'] != expected or (allowed and run['status'] not in allowed):
                raise Conflict('This run has changed. Refresh it and review before submitting again.')
            run.update(changes)
            run['version']+=1
            run['updated_at']=now()
            if event:
                run['events'].append({'label':event,'at':run['updated_at']})
            self._write(run)
            return run

    def recover(self):
        with self.lock:
            for path in self.root.glob('*/run.json'):
                run=self._read(path.parent.name)
                if run and run['status'] in ('queued','analysing','planning'):
                    self.change(run['id'],run['owner'],run['version'],
                        {'status':'failed','error':'Processing was interrupted by a server restart. Create a new run.'},event='Interrupted run stopped')
