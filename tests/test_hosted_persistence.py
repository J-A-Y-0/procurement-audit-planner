"""Restart checks without spending API credit or requiring a hosted database."""
import copy
import io
import json
import shutil
import zipfile
import pytest
from webapp.budget import ApiBudget, BudgetError
from webapp.store import RunStore


class MemoryPersistence:
    def __init__(self):
        self.values = {}
        self.records = {}

    def get(self, key): return self.values.get(key)
    def put(self, key, value): self.values[key] = value
    def save_run(self, rid, record, archive=None):
        old = self.records.get(rid, (None, None))[1]
        self.records[rid] = (record, archive if archive is not None else old)
    def runs(self):
        return [(rid, record, archive) for rid, (record, archive) in self.records.items()]


@pytest.mark.parametrize('status', ['awaiting_scope', 'awaiting_signoff', 'signed_off', 'requires_model'])
def test_human_gate_and_artifacts_survive_empty_local_disk(tmp_path, status):
    backend = MemoryPersistence()
    root = tmp_path / 'runs'
    store = RunStore(root, persistence=backend)
    run = store.create('owner', 'Restart review', 'live')
    out = store.folder(run['id']) / 'workspace/outputs'
    out.mkdir(parents=True)
    (out / 'review.md').write_text('Verified working paper')
    changed = store.change(run['id'], 'owner', run['version'], {'status': status, 'decisions': [{'id': 'R-01'}]})
    shutil.rmtree(root)
    restored = RunStore(root, persistence=backend)
    restored.recover()
    assert restored.get(run['id'], 'owner') == changed
    assert restored.get(run['id'], 'another-browser') is None
    assert (restored.folder(run['id']) / 'workspace/outputs/review.md').read_text() == 'Verified working paper'


def test_inflight_restart_is_blocked_and_previous_checkpoint_retained(tmp_path):
    backend = MemoryPersistence()
    store = RunStore(tmp_path / 'old', persistence=backend)
    run = store.create('owner', 'Restart', 'live')
    checkpoint = store.folder(run['id']) / 'evidence.txt'
    checkpoint.write_text('scope evidence')
    run = store.change(run['id'], 'owner', run['version'], {'status': 'awaiting_scope'})
    store.change(run['id'], 'owner', run['version'], {'status': 'planning'})
    restored = RunStore(tmp_path / 'fresh', persistence=backend)
    restored.recover()
    assert restored.get(run['id'], 'owner')['status'] == 'failed'
    assert (restored.folder(run['id']) / 'evidence.txt').read_text() == 'scope evidence'


def test_budget_completed_and_uncertain_charges_survive_empty_disk(tmp_path):
    backend = MemoryPersistence()
    budget = ApiBudget(tmp_path / 'old/budget.json', .024, persistence=backend)
    first = budget.reserve('claude-haiku-5-5', 50000, 18000)
    budget.settle(first, {'input_tokens': 50000, 'output_tokens': 1000})
    uncertain = budget.reserve('claude-haiku-5-5', 50000, 18000)
    restored = ApiBudget(tmp_path / 'fresh/budget.json', .024, persistence=backend)
    assert restored.read()['committed_micro_usd'] == 5500
    assert uncertain in restored.read()['reservations']
    with pytest.raises(BudgetError, match='budget cannot cover'):
        restored.reserve('claude-haiku-5-5', 50000, 18000)
    assert not (tmp_path / 'fresh/budget.json').exists()


def test_storage_failure_never_acknowledges_a_new_gate_or_reservation(tmp_path):
    backend = MemoryPersistence()
    store = RunStore(tmp_path / 'runs', persistence=backend)
    run = store.create('owner', 'Failure', 'live')
    before = copy.deepcopy(store.get(run['id'], 'owner'))
    def fail(*args): raise RuntimeError('Database unavailable')
    backend.save_run = fail
    with pytest.raises(RuntimeError):
        store.change(run['id'], 'owner', run['version'], {'status': 'awaiting_scope'})
    assert store.get(run['id'], 'owner') == before
    backend.put = fail
    budget = ApiBudget(tmp_path / 'budget.json', 1, persistence=backend)
    with pytest.raises(RuntimeError): budget.reserve('claude-haiku-5-5', 10, 18000)
    assert not (tmp_path / 'budget.json').exists()


def test_invalid_archive_cannot_escape_run_folder(tmp_path):
    backend = MemoryPersistence()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z: z.writestr('../outside.txt', 'bad')
    backend.records['a' * 32] = (json.dumps({'id': 'a' * 32}).encode(), buffer.getvalue())
    with pytest.raises(ValueError, match='Invalid stored'):
        RunStore(tmp_path / 'runs', persistence=backend)
    assert not (tmp_path / 'runs/outside.txt').exists()


def test_database_health_failure_is_visible_to_host(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from webapp.main import create_app
    from webapp import persistence
    backend = MemoryPersistence()
    backend.ping = lambda: None
    backend.close = lambda: None
    monkeypatch.setenv('DATABASE_URL', 'test-only')
    monkeypatch.setattr(persistence, 'PostgresPersistence', lambda url: backend)
    with TestClient(create_app(tmp_path / 'runs', provider=None)) as client:
        assert client.get('/healthz').status_code == 200
        def fail(): raise RuntimeError('private database error')
        backend.ping = fail
        response = client.get('/healthz')
        assert response.status_code == 503
        assert 'private' not in response.text
