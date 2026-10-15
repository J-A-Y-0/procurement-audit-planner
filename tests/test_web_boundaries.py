from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
from webapp.main import create_app
from webapp.store import RunStore
from webapp.models import Scope

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path):
    app=create_app(tmp_path/'runs',ROOT,provider=None)
    with TestClient(app) as c:
        c.get('/api/config')
        yield c,app

def seed(c,app,status='awaiting_scope'):
    import hashlib
    owner=hashlib.sha256(c.cookies['audit_session'].encode()).hexdigest()
    r=app.state.store.create(owner,'Boundary test','live')
    r=app.state.store.change(r['id'],owner,r['version'],{'status':status,
       'risks':[{'id':'R-01','recommend_in_scope':True}]})
    out=app.state.engine.work(r['id'])/'outputs';out.mkdir(parents=True)
    return r,owner,out

def test_http_boundaries_and_sanitized_documents(client):
    c,app=client
    assert c.post('/api/runs',json={'title':'x'},headers={'Origin':'https://evil.example'}).status_code==403
    assert c.post('/api/runs',json={'title':'x'},headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
    assert c.post('/api/runs',content='x',headers={'Content-Type':'text/plain'}).status_code==415
    assert c.post('/api/runs',content='x'*65537,headers={'Content-Type':'application/json'}).status_code==413
    assert c.post('/api/runs',json={'title':'x','unknown':True}).status_code==422
    r,owner,out=seed(c,app)
    (out/'risk-register.md').write_text('# Test\n<script>alert(1)</script><img src=x onerror=alert(2)>[bad](javascript:alert)\n')
    url=f"/runs/{r['id']}/documents/risk-register.md"
    html=c.get(url)
    assert html.status_code==200
    assert '<script>' not in html.text and '<img' not in html.text and 'href="javascript:' not in html.text
    for path in ['run.json','../run.json','%2e%2e%2frun.json','.env','execution.log']:
        assert c.get(f"/api/runs/{r['id']}/artifacts/{path}").status_code==404
    body={'expected_version':r['version'],'reviewer':'Test','date':'2026-10-15','decision':'sign_off'}
    assert c.post(f"/api/runs/{r['id']}/signoff",json=body).status_code==409
    assert c.get('/api/runs/not-a-real-id').status_code==404
    assert c.get('/api/runs').json()['runs'][0].get('owner') is None
    assert 'HttpOnly' in c.get('/').headers.get('set-cookie','') or c.cookies.get('audit_session')

def test_explicit_scope_and_no_automatic_signature(client):
    c,app=client;r,owner,out=seed(c,app)
    base={'expected_version':r['version'],'reviewer':'Test','date':'2026-10-15'}
    url=f"/api/runs/{r['id']}/scope"
    for decision in [[],[{'id':'R-02','decision':'approve','in_scope':True}],
        [{'id':'R-01','decision':'reject','in_scope':False,'comment':''}],
        [{'id':'R-01','decision':'approve','in_scope':False}],
        [{'id':'R-01','decision':'amend','in_scope':True}]]:
        assert c.post(url,json={**base,'decisions':decision}).status_code==422
    assert app.state.store.get(r['id'],owner)['decisions'] is None
    assert c.post(url,json={**base,'reviewer':'A\nB','decisions':[{'id':'R-01','decision':'approve','in_scope':True}]}).status_code==422


def test_waiting_state_survives_restart(tmp_path):
    store=RunStore(tmp_path)
    r=store.create('owner','test','example')
    r=store.change(r['id'],'owner',r['version'],{'status':'awaiting_scope'})
    RunStore(tmp_path).recover()
    assert store.get(r['id'],'owner')==r


def test_return_requires_explanation(client):
    c,app=client;r,owner,out=seed(c,app,'awaiting_signoff')
    (out/'review.md').write_text('# Review\n\n## Auditor sign-off\n\nAwaiting explicit human sign-off.\n')
    payload={'expected_version':r['version'],'reviewer':'Test Reviewer','date':'2026-10-15','decision':'return','comment':''}
    assert c.post(f"/api/runs/{r['id']}/signoff",json=payload).status_code==422
    assert app.state.store.get(r['id'],owner)['status']=='awaiting_signoff'
    assert c.get(f"/api/runs/{r['id']}/download").status_code==409


def test_missing_key_blocks_generation(client):
    c,app=client
    assert c.get('/api/config').json()['live_available'] is False
    assert c.post('/api/runs',json={'title':'Missing key'}).status_code==409


def test_cached_extraction_requires_exact_verified_source_files(tmp_path):
    from webapp.engine import EvidenceWorkspace
    import hashlib
    (tmp_path/'data').mkdir();(tmp_path/'evidence').mkdir()
    data=tmp_path/'data/source.txt';data.write_text('original evidence')
    (tmp_path/'evidence/source-manifest.json').write_text(json.dumps({'files':[{'file':'data/source.txt','sha256':hashlib.sha256(data.read_bytes()).hexdigest()}]}))
    EvidenceWorkspace(tmp_path)
    data.write_text('changed evidence')
    with pytest.raises(ValueError,match='source manifest'):EvidenceWorkspace(tmp_path)
