from pathlib import Path
import time
import zipfile
import io
import pytest
from tests.web_fixtures import wait,FixtureProvider

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(tmp_path):
    from webapp.main import create_app
    return create_app(tmp_path / 'runs', ROOT,provider=FixtureProvider())

@pytest.mark.parametrize('scope_change', ['reject', 'amend', 'approve'])
def test_live_workflow_and_human_gates(app, scope_change):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        assert c.post('/api/runs', json={'title':'Test run','mode':'example'}).status_code == 422
        r = c.post('/api/runs', json={'title':'Test run','mode':'live'})
        assert r.status_code == 202, r.text
        rid=r.json()['id']
        assert c.get(f'/api/runs/{rid}/download').status_code == 409
        run=wait(c,rid,'awaiting_scope')
        assert run['decisions'] is None and run['signoff'] is None
        assert len(run['risks']) == 7
        assert run['dataset_summary']['rows_retained'] == 8534
        decisions=[{'id':x['id'],'decision':'approve','comment':'','in_scope':True} for x in run['risks']]
        if scope_change != 'approve':
            decisions[-1].update(decision=scope_change,comment='Excluded for this test',in_scope=False)
        body={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15','decisions':decisions}
        r=c.post(f'/api/runs/{rid}/scope',json=body)
        assert r.status_code == 202,r.text
        assert c.post(f'/api/runs/{rid}/scope',json=body).status_code == 409
        run=wait(c,rid,'awaiting_signoff')
        assert len(run['qa']) == 4 and all(x['result']=='PASS' for x in run['qa'])
        assert run['signoff'] is None
        review=next(x for x in run['artifacts'] if x['name']=='review.md')
        assert 'Jay Yu' not in c.get(review['url']).text
        assert c.get(f'/api/runs/{rid}/download').status_code == 409
        payload={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15','decision':'sign_off','comment':'Approved for test'}
        r=c.post(f'/api/runs/{rid}/signoff',json=payload)
        assert r.status_code == 200,r.text
        assert r.json()['status']=='signed_off'
        assert c.post(f'/api/runs/{rid}/signoff',json=payload).status_code==409
        z=zipfile.ZipFile(io.BytesIO(c.get(f'/api/runs/{rid}/download').content))
        assert 'outputs/audit-program.md' in z.namelist()
        assert 'Test Reviewer' in z.read('outputs/review.md').decode()
        plan=__import__('json').loads(z.read('outputs/audit-plan.json'))
        assert len(plan['risks'])==(7 if scope_change=='approve' else 6)
        assert 'Live AI run' in z.read('README.md').decode()
        if scope_change=='approve':
            assert run['figures']['sample_occurrences']==267
            assert run['figures']['unique_payments']==236
            assert run['figures']['unique_sample_gbp']==12163778.11
        with TestClient(app) as other:
            assert other.get(f'/api/runs/{rid}').status_code==404
            assert other.get(f'/api/runs/{rid}/download').status_code==404


def test_store_restart_and_versions(tmp_path):
    from webapp.store import RunStore, Conflict
    s=RunStore(tmp_path)
    r=s.create('owner','test','example')
    with pytest.raises(Conflict):
        s.change(r['id'],'owner',99,{'status':'planning'})
    s.recover()
    assert s.get(r['id'],'owner')['status']=='failed'
    assert s.get(r['id'],'other') is None


def test_all_excluded_is_recorded_without_a_fabricated_plan(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        r=c.post('/api/runs',json={'title':'No scope','mode':'live'}).json()
        run=wait(c,r['id'],'awaiting_scope')
        body={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15',
            'decisions':[{'id':x['id'],'decision':'reject','comment':'Excluded | pending review','in_scope':False} for x in run['risks']]}
        response=c.post(f"/api/runs/{r['id']}/scope",json=body)
        assert response.status_code==202,response.text
        run=response.json()
        assert run['status']=='requires_model'
        assert run['signoff'] is None
        assert not any(x['name'] in ('audit-plan.json','risk-register.md') for x in run['artifacts'])
        scope_doc=next(x for x in run['artifacts'] if x['name']=='scope-result.md')
        assert 'All proposed risks were excluded' in c.get(scope_doc['url']).text
        assert c.get(f"/api/runs/{r['id']}/artifacts/risk-register.md").status_code==404
        assert c.get(f"/api/runs/{r['id']}/download").status_code==409
