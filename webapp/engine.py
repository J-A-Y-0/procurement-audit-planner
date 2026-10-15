"""Run the Part A tools and live Anthropic roles in isolated workspaces."""
import csv
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .store import Conflict
from .provider import ProviderError
from .live import LiveTeam, LIVE_NOTICE

LOG=logging.getLogger('audit')

def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def cell(value):
    return str(value).replace('|','&#124;').replace('\n',' ').replace('\r',' ')

class EvidenceWorkspace:
    """Copy fixed source evidence and its verified extraction cache."""
    def __init__(self, project):
        self.project=Path(project)
        expected=read(self.project/'evidence/source-manifest.json')
        self.hashes={entry['file']:entry['sha256'] for entry in expected['files']}
        actual={p.relative_to(self.project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (self.project/'data').rglob('*') if p.is_file()}
        if actual!=self.hashes:
            raise ValueError('The bundled data does not match the verified source manifest; restore the supplied files before using the extraction cache.')

    def populate(self, work):
        # Copies, never symlinks: script ROOT resolution must stay inside this run.
        for name in ('data','scripts','.claude/skills','.claude/agents'):
            shutil.copytree(self.project/name,work/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for relative, digest in self.hashes.items():
            if hashlib.sha256((work/relative).read_bytes()).hexdigest()!=digest:
                raise ValueError('Bundled source files changed while preparing the run.')
        out=work/'outputs';out.mkdir()
        for name in ('rules.json','history.json'):
            shutil.copy2(self.project/'outputs'/name,out/name)
        write(work/'source-manifest.json',self.hashes)
        (out/'run-provenance.md').write_text('# Run provenance\n\n'+LIVE_NOTICE+'\n')

class AuditEngine:
    def __init__(self, project, store, provider=None):
        self.project=Path(project).resolve();self.store=store;self.provider=provider
        self.source=EvidenceWorkspace(self.project)
        self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='audit')
        self.store.recover()
        # Free hosts have no operator shell. Keep failures in private host logs
        # as well as the checkpoint, without exposing them as public artifacts.
        for path in self.store.root.glob('*/error.log'):
            LOG.error('Stored failure for run %s:\n%s',path.parent.name,path.read_text()[-12000:])

    def close(self):
        self.pool.shutdown(wait=True)

    def work(self,rid):
        return self.store.folder(rid)/'workspace'

    def command(self,work,*args):
        p=subprocess.run([sys.executable,*args],cwd=work,capture_output=True,text=True,timeout=600)
        with (work.parent/'execution.log').open('a') as f:
            f.write('\n$ '+ ' '.join(args)+'\n'+p.stdout+p.stderr)
        if p.returncode:
            raise RuntimeError('A required validation failed. The run is blocked; the operator can inspect its execution log.')
        return p.stdout

    def submit(self,run,fn):
        self.pool.submit(self._guard,run['id'],run['owner'],fn)

    def _guard(self,rid,owner,fn):
        try:
            fn(rid,owner)
        except Exception as error:
            import traceback
            LOG.exception('Audit run %s stopped',rid)
            (self.store.folder(rid)/'error.log').write_text(traceback.format_exc())
            run=self.store.get(rid,owner)
            self.store.change(rid,owner,run['version'],{'status':'failed',
                'error':str(error) if isinstance(error,ProviderError) else 'A required analysis or validation did not finish successfully. The run is blocked; ask the operator to inspect its private log.'},event='Run blocked')

    def create(self,owner,title,mode):
        if self.provider is None:
            raise Conflict('Set ANTHROPIC_API_KEY on the server to start a live review.')
        with self.store.lock:
            if mode=='live':
                records=[self.store._read(p.parent.name) for p in self.store.root.glob('*/run.json')]
                live=[x for x in records if x and x.get('mode')=='live']
                limit=max(1,int(os.environ.get('AUDIT_LIVE_RUN_LIMIT','12')))
                if len(live)>=limit:
                    raise Conflict('This hosted application has reached its live review allowance. Ask the operator to extend the allowance.')
                if any(x['status'] in ('queued','analysing','planning') for x in live):
                    raise Conflict('Another live review is processing. Please wait before starting a new one.')
            run=self.store.create(owner,title,mode)
        self.submit(run,self.analyse)
        return run

    def analyse(self,rid,owner):
        r=self.store.get(rid,owner)
        self.store.change(rid,owner,r['version'],{'status':'analysing'},event='Recomputing the supplied data')
        work=self.work(rid);work.mkdir()
        self.source.populate(work)
        for label,cmd in [
            ('Cleaning the supplied payments',('scripts/clean.py',)),
            ('Calculating procurement indicators',('scripts/analyse.py',)),
            ('Reconciling analysis totals',('scripts/selfcheck.py',)),
            ('Verifying procurement rule quotations',('.claude/skills/extract-rules/verify_quotes.py','outputs/rules.json','data/contract-rules.pdf')),
            ('Verifying audit history quotations',('scripts/verify_history.py','outputs/history.json','data/committee'))]:
            r=self.store.get(rid,owner)
            self.store.change(rid,owner,r['version'],{},event=label)
            self.command(work,*cmd)
        self.team(rid,owner).assess()
        population=read(work/'outputs/analytics.json')['population']
        ratings=read(work/'outputs/risk-ratings.json')['risks']
        bands={}
        for line in (work/'outputs/risk-register.md').read_text().splitlines():
            cols=[c.strip() for c in line.strip('|').split('|')]
            if len(cols)>=9 and re.fullmatch(r'R-\d+',cols[0]): bands[cols[0]]=cols[6]
        risks=[]
        for x in ratings:
            score=x['likelihood']['score']*x['impact']['score']
            risks.append({**{k:x[k] for k in ('id','title','risk','proposed_focus','recommend_in_scope')},
                'likelihood':x['likelihood']['score'],'impact':x['impact']['score'],'score':score,
                'band':bands[x['id']]})
        r=self.store.get(rid,owner)
        self.store.change(rid,owner,r['version'],{'status':'awaiting_scope','risks':risks,
            'dataset_summary':{'rows_raw':population['rows_raw'],'rows_retained':population['rows_after_exclusions'],
                               'total_gbp':population['total_gbp'],'months':population['months_covered']}},
            event='Evidence verified; human scope decisions required')

    def scope(self,rid,owner,payload):
        with self.store.lock:
            r=self.store.get(rid,owner)
            if not r: raise KeyError(rid)
            if r['version']!=payload.expected_version or r['status']!='awaiting_scope':
                raise Conflict('This run has changed. Refresh it and review before submitting again.')
            decisions=[d.model_dump() for d in payload.decisions]
            current={x['id']:x for x in r['risks']}
            if len(decisions)!=len(current) or {x['id'] for x in decisions}!=set(current):
                raise ValueError('Record exactly one decision for every risk.')
            for d in decisions:
                if d['decision']=='approve' and d['in_scope']!=current[d['id']]['recommend_in_scope']:
                    raise ValueError('Use Amend scope to change the proposed inclusion.')
                if d['decision']=='reject' and (not d['comment'].strip() or d['in_scope']):
                    raise ValueError('A rejected risk needs a reason and must be excluded.')
                if d['decision']=='amend' and d['in_scope']==current[d['id']]['recommend_in_scope']:
                    raise ValueError('An amendment must change the proposed scope. Use Approve to retain it.')
            status='planning' if any(d['in_scope'] and d['decision']!='reject' for d in decisions) else 'requires_model'
            prepared={**r,'decisions':decisions,'scope_reviewer':payload.reviewer,'scope_date':payload.date.isoformat()}
            # A failed artifact write must not strand the run in a processing state.
            self.apply_decisions(prepared)
            r=self.store.change(rid,owner,r['version'],{'status':status,'decisions':decisions,
                'scope_reviewer':payload.reviewer,'scope_date':payload.date.isoformat(),
                'error':None if status=='planning' else 'No risks remain in scope. A new model-assisted assessment is required to propose a different plan.'},
                event='Human scope decisions recorded')
            if status=='planning':
                self.submit(r,self.plan)
            else:
                out=self.work(rid)/'outputs'
                summary='# Scope decision: no risks retained\n\n'+LIVE_NOTICE+'\n\nReviewer: '+cell(r['scope_reviewer'])+'\nDate: '+r['scope_date']+'\n\nAll proposed risks were excluded by the auditor. No audit plan or final sign-off is available. A new model-assisted assessment is required before a different scope can be proposed.\n\n'
                summary+='| Risk | Decision | Reason |\n|---|---|---|\n'
                summary+='\n'.join('| '+' | '.join(map(cell,[d['id'],d['decision'],d['comment'] or 'Excluded from scope']))+' |' for d in decisions)+'\n'
                (out/'scope-result.md').write_text(summary)
                self.store._write(r)
            return r

    def apply_decisions(self,r):
        out=self.work(r['id'])/'outputs';ratings=read(out/'risk-ratings.json')
        risks={x['id']:x for x in ratings['risks']};changes=[];rows=[]
        for d in r['decisions']:
            x=risks[d['id']];comment=d['comment'].strip()
            if d['decision']=='amend':
                comment=json.dumps({'recommend_in_scope':d['in_scope']})
                x['recommend_in_scope']=d['in_scope'];changes.append({'id':x['id'],'action':'amended'})
            elif d['decision']=='reject':
                ratings.setdefault('excluded',[]).append({'id':x['id'],'reason':comment.replace('\n',' ').replace('\r',' ')})
                changes.append({'id':x['id'],'action':'rejected'})
            rows.append('| '+' | '.join(map(cell,[x['id'],x['title'],str(x['likelihood']['score']*x['impact']['score']),
                'In' if d['in_scope'] else 'Out',d['decision'],comment]))+' |')
        rejected={d['id'] for d in r['decisions'] if d['decision']=='reject'}
        ratings['risks']=[x for x in ratings['risks'] if x['id'] not in rejected]
        ratings['revision']={'number':1,'changes':changes}
        write(out/'risk-ratings.json',ratings)
        (out/'auditor-comments.md').write_text('# Auditor scope decisions\n\nReviewer: '+cell(r['scope_reviewer'])+'\nDate: '+r['scope_date']+
            '\n\n| ID | Risk | Current rating | Scope | Decision | Comment |\n|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n')
        # Preserve optional amendment notes separately; the validator requires exact JSON in its Comment cell.
        write(out/'human-decisions.json',{'reviewer':r['scope_reviewer'],'date':r['scope_date'],'decisions':r['decisions']})

    def plan(self,rid,owner):
        r=self.store.get(rid,owner);work=self.work(rid);out=work/'outputs'
        self.command(work,'.claude/skills/risk-assessment/build_register.py')
        self.command(work,'.claude/skills/audit-program/build_pack.py','--gate')
        feedback='\n'.join(x['comment'] for x in r.get('return_history',[]))
        check,human,summary=self.team(rid,owner).plan_and_review(feedback)
        self.finish_plan(rid,owner,check,LIVE_NOTICE,summary,human)

    def team(self,rid,owner):
        def event(text):
            r=self.store.get(rid,owner)
            self.store.change(rid,owner,r['version'],{},event=text)
        return LiveTeam(self.work(rid),self.project,self.provider,self.command,event)

    def finish_plan(self,rid,owner,check,notice,summary='',human=None):
        out=self.work(rid)/'outputs'
        qa=[]
        for line in check.splitlines():
            parts=[x.strip() for x in line.strip('|').split('|')]
            if len(parts)==3 and parts[1] in ('PASS','FAIL'):
                qa.append(dict(zip(('name','result','summary'),parts)))
        if len(qa)!=4 or any(x['result']!='PASS' for x in qa):
            raise RuntimeError('Incomplete QA results')
        (out/'checks.txt').write_text(check)
        review='# Run review\n\n'+notice+'\n\n'+summary+'\n\n'+check+'\n\n## Auditor sign-off\n\nAwaiting explicit human sign-off.\n'
        (out/'review.md').write_text(review)
        f=read(out/'pack-figures.json')['figures'];unique={};occurrences=0
        for path in (out/'samples').glob('*.csv'):
            for row in csv.DictReader(path.open()):
                occurrences+=1;unique[row['row_id']]=float(row['amount'])
        figures={'sample_occurrences':occurrences,'unique_payments':len(unique),'unique_sample_gbp':round(sum(unique.values()),2),
                 'controls':f['controls'],'tests':f['tests'],'pbc_requests':f['pbc_items']}
        write(out/'run-summary.json',figures)
        r=self.store.get(rid,owner)
        self.store.change(rid,owner,r['version'],{'status':'awaiting_signoff','qa':qa,'figures':figures,'auditor_points':human or []},
            event='Planning pack and all deterministic checks completed; human sign-off required')

    def signoff(self,rid,owner,payload):
        with self.store.lock:
            r=self.store.get(rid,owner)
            if not r: raise KeyError(rid)
            if r['version']!=payload.expected_version or r['status']!='awaiting_signoff':
                raise Conflict('This run has changed or is not ready for sign-off.')
            if r.get('auditor_points') and payload.decision=='sign_off' and not payload.comment.strip():
                raise Conflict('Explain your decision on the points flagged for the auditor before signing off.')
            if payload.decision=='return' and len(r.get('return_history',[]))>=3:
                raise Conflict('This run has reached its revision limit. Start a new assessment for further changes.')
            signoff=payload.model_dump(mode='json');signoff.pop('expected_version')
            out=self.work(rid)/'outputs';path=out/'review.md'
            text=path.read_text().split('## Auditor sign-off')[0]
            text+='## Auditor sign-off\n\nReviewer: '+cell(payload.reviewer)+'\nDate: '+payload.date.isoformat()+\
                  '\nDecision: '+payload.decision+'\nComment: '+cell(payload.comment)+'\n'
            if payload.decision=='return':
                text+='\nReturned to the team for revision.\n'
            path.write_text(text)
            if payload.decision=='return':
                history=r.get('return_history',[])+[signoff]
                dump_path=out/f'return-{len(history)}.json';write(dump_path,signoff)
                updated=self.store.change(rid,owner,r['version'],{'status':'planning','signoff':None,'return_history':history,'qa':[],'figures':{}},event='Human returned the plan; team revision started')
                self.submit(updated,self.plan)
                return updated
            return self.store.change(rid,owner,r['version'],{'status':'signed_off' if payload.decision=='sign_off' else 'returned','signoff':signoff},event='Human '+('sign-off recorded' if payload.decision=='sign_off' else 'return recorded'))
