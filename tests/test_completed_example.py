"""A public snapshot must not become access to another browser's live review."""
import hashlib
import io
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient
from webapp.main import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_completed_example_is_public_read_only_and_does_not_create_a_run(tmp_path):
    with TestClient(create_app(tmp_path/'runs', ROOT, provider=None)) as client:
        page = client.get('/example/')
        assert page.status_code == 200
        assert 'Completed example · Read-only' in page.text
        assert 'Jay Yu' in page.text and '2026-10-15' in page.text
        assert all(f'<td>{check}</td>' in page.text for check in ('quotes', 'numbers', 'trace', 'samples'))
        assert page.text.count('<td>PASS</td>') >= 4
        archive = client.get('/example/audit-pack.zip')
        assert archive.status_code == 200
        assert hashlib.sha256(archive.content).hexdigest() == '3915978ee2ff950dba9593e87adbf707adc59aa629a19124bf3c830d2151525e'
        with zipfile.ZipFile(io.BytesIO(archive.content)) as pack:
            assert pack.testzip() is None
            assert 'Decision: sign_off' in pack.read('outputs/review.md').decode()
            assert 'outputs/team-messages.json' in pack.namelist()
        assert client.post('/example/', json={}).status_code == 405
        assert client.get('/api/runs').json() == {'runs': []}
        assert client.get('/api/runs/a88c49fe9b8c44ef88449cc258ce9b89').status_code == 404
