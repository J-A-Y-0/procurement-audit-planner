import copy,json,time
from pathlib import Path
from fastapi.testclient import TestClient
from tests.web_fixtures import wait,FixtureProvider

ROOT=Path(__file__).resolve().parents[1]



def test_live_pipeline_uses_new_role_outputs_and_never_inherits_approvals(tmp_path):
    from webapp.main import create_app
    provider=FixtureProvider()
    app=create_app(tmp_path/'runs',ROOT,provider=provider)
    with TestClient(app) as c:
        assert c.get('/api/config').json()['live_available'] is True
        r=c.post('/api/runs',json={'title':'Live test fixture','mode':'live'})
        assert r.status_code==202,r.text
        run=wait(c,r.json()['id'],'awaiting_scope')
        assert run['decisions'] is None and run['signoff'] is None
        assert provider.roles==['risk-assessor']
        decisions=[{'id':r['id'],'decision':'approve','comment':'','in_scope':r['recommend_in_scope']} for r in run['risks']]
        c.post('/api/runs/'+run['id']+'/scope',json={'expected_version':run['version'],
            'reviewer':'Test Reviewer','date':'2026-10-15','decisions':decisions})
        run=wait(c,run['id'],'awaiting_signoff')
        assert provider.roles==['risk-assessor','planner','challenger','qa-reviewer']
        assert all(q['result']=='PASS' for q in run['qa'])
        assert run['signoff'] is None
        docs={a['name']:a for a in run['artifacts']}
        assert 'agent-activity.json' in docs and 'team-messages.json' in docs
        text=c.get(docs['challenges.md']['url']).text
        assert 'No actionable' in text and 'recorded reference' not in text.lower()
        assert 'Live AI run' in c.get(docs['run-provenance.md']['url']).text
        assert c.get('/api/runs/'+run['id']+'/download').status_code==409

class ChallengeProvider(FixtureProvider):
    def __init__(self):super().__init__();self.plans=0;self.reviews=0
    def generate_json(self,role,instructions,context):
        if role not in ('planner','challenger'):return super().generate_json(role,instructions,context)
        self.roles.append(role)
        if role=='planner':
            self.plans+=1
            plan=json.loads((ROOT/'outputs/audit-plan.json').read_text())
            value=plan if self.plans!=2 else {'plan':plan,'responses':[{'id':1,'decision':'declined','explanation':'The current test already inspects the prior approval.'}]}
        else:
            self.reviews+=1
            value={'summary':'Reviewed the test evidence.','challenges':[{'type':'test','risk':'R-01','challenge':'Verify the prior exception approval is tested.','evidence':'CPR-16; T-01.2','ask':'Inspect the approval requirement.'}]} if self.reviews==1 else {'summary':'Existing coverage verified.','challenges':[],
                'statuses':[{'id':1,'status':'declined','resolution':'T-01.2 explicitly tests prior approval.'}]}
        return value,{'role':role,'model':self.model,'completed':True,'response_id':'fixture-'+str(len(self.roles))}


def test_real_builders_handle_role_messages_and_return_revision(tmp_path):
    from webapp.main import create_app
    provider=ChallengeProvider();app=create_app(tmp_path/'runs',ROOT,provider=provider)
    with TestClient(app) as c:
        run=c.post('/api/runs',json={'title':'Team test','mode':'live'}).json()
        run=wait(c,run['id'],'awaiting_scope')
        c.post('/api/runs/'+run['id']+'/scope',json={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15',
            'decisions':[{'id':r['id'],'decision':'approve','in_scope':r['recommend_in_scope'],'comment':''} for r in run['risks']]})
        run=wait(c,run['id'],'awaiting_signoff')
        messages=next(a for a in run['artifacts'] if a['name']=='team-messages.json')
        assert 'CHALLENGE #1' in c.get(messages['url']).text
        assert 'RESPONSE #1' in c.get(messages['url']).text
        response=c.post('/api/runs/'+run['id']+'/signoff',json={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15',
            'decision':'return','comment':'Please refine the wording while preserving scope.'})
        assert response.status_code==200,response.text
        assert response.json()['status']=='planning'
        run=wait(c,run['id'],'awaiting_signoff')
        assert run['signoff'] is None and len(run['return_history'])==1
        assert c.get('/api/runs/'+run['id']+'/download').status_code==409


def test_live_allowance_and_concurrent_model_work_are_bounded(tmp_path,monkeypatch):
    from webapp.store import RunStore,Conflict
    from webapp.engine import AuditEngine
    import pytest
    store=RunStore(tmp_path/'runs');provider=FixtureProvider()
    engine=AuditEngine(ROOT,store,provider)
    try:
        active=store.create('other-owner','Existing work','live')
        with pytest.raises(Conflict,match='Another live review'):
            engine.create('new-owner','New','live')
        store.change(active['id'],'other-owner',active['version'],{'status':'failed'})
        monkeypatch.setenv('AUDIT_LIVE_RUN_LIMIT','1')
        with pytest.raises(Conflict,match='allowance'):
            engine.create('new-owner','New','live')
    finally:engine.close()


def test_challenger_must_resolve_every_evidence_reference():
    from webapp.live import LiveTeam
    from webapp.provider import ProviderError
    import pytest
    team=LiveTeam(ROOT,ROOT,FixtureProvider(),lambda *args:'')
    issue={'type':'test','risk':'R-01','challenge':'Check the evidence','ask':'Verify the source'}
    for evidence in ('$.this_metric_does_not_exist','CPR-16; $.missing_metric','CPR-999; T-01.2'):
        with pytest.raises(ProviderError):team.valid_findings({'challenges':[{**issue,'evidence':evidence}]},8)
    assert len(team.valid_findings({'challenges':[{**issue,'evidence':'CPR-16; $.population.rows_raw'}]},8))==1


def test_risk_web_contract_repaired_and_missing_excluded_defaults_safely(tmp_path):
    from webapp.live import LiveTeam
    out=tmp_path/'workspace/outputs';out.mkdir(parents=True)
    class RiskProvider:
        def __init__(self):self.calls=0
        def generate_json(self,role,instructions,context):
            self.calls+=1
            return {'risks':[{'id':'R-1' if self.calls==1 else 'R-01'}]},{'role':role,'completed':True,'response_id':'fixture'}
    provider=RiskProvider();commands=[]
    team=LiveTeam(out.parent,ROOT,provider,lambda *args:commands.append(args))
    result=team.validated('risk-assessor','test','test','risk-ratings.json',('fixture-check',))
    assert provider.calls==2 and len(commands)==1
    assert result['excluded']==[]
    assert json.loads((out/'risk-ratings.json').read_text())['risks'][0]['id']=='R-01'


def test_qa_failure_is_sent_to_planner_and_correction_rechecked(tmp_path):
    from webapp.main import create_app
    provider=FixtureProvider();app=create_app(tmp_path/'runs',ROOT,provider=provider)
    engine=app.state.engine;original=engine.command;checks=[]
    def fail_first_check(work,*args):
        if args==('scripts/checks/run_checks.py',):
            checks.append(args)
            if len(checks)==1:
                with (work.parent/'execution.log').open('a') as f:f.write('\n$ scripts/checks/run_checks.py\nFAIL: injected offline QA fixture\n')
                raise RuntimeError('Injected offline QA fixture')
        return original(work,*args)
    engine.command=fail_first_check
    with TestClient(app) as c:
        run=c.post('/api/runs',json={'title':'QA repair fixture','mode':'live'}).json()
        run=wait(c,run['id'],'awaiting_scope')
        c.post('/api/runs/'+run['id']+'/scope',json={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15',
            'decisions':[{'id':r['id'],'decision':'approve','in_scope':r['recommend_in_scope'],'comment':''} for r in run['risks']]})
        run=wait(c,run['id'],'awaiting_signoff')
        assert len(checks)==2
        assert provider.roles.count('planner')==2 and provider.roles.count('qa-reviewer')==2
        artifact=next(x for x in run['artifacts'] if x['name']=='team-messages.json')
        messages=c.get(artifact['url']).json()
        assert any(x['from']=='qa-reviewer' and x['to']=='planner' and 'FAIL' in x['message'] for x in messages)


def test_model_projection_preserves_metrics_and_keeps_original_row_ids():
    from webapp.live import LiveTeam
    team=LiveTeam(ROOT,ROOT,FixtureProvider(),lambda *args:'')
    text=team.inputs()
    projected=json.JSONDecoder().raw_decode(text.split('FILE analytics.json\n',1)[1])[0]
    original=json.loads((ROOT/'outputs/analytics.json').read_text())
    assert projected['population']==original['population']
    original_top=original['tests']['split_purchases']['500000']['top20_windows'][0]
    projected_top=projected['tests']['split_purchases']['500000']['top20_windows'][0]
    assert 'row_ids' in original_top and 'row_ids' not in projected_top
    assert projected_top=={k:v for k,v in original_top.items() if k!='row_ids'}


def test_challenger_corrects_uncited_review_without_rebuilding_plan(tmp_path):
    from webapp.live import LiveTeam
    out=tmp_path/'workspace/outputs';out.mkdir(parents=True)
    import shutil
    for name in ('rules.json','history.json','analytics.json','audit-plan.json'):
        shutil.copy2(ROOT/'outputs'/name,out/name)
    class Reviewer:
        calls=0
        def generate_json(self,role,instructions,context):
            self.calls+=1
            if self.calls==2:assert 'ACTUAL REVIEW VALIDATOR ERROR' in context
            return {'summary':'Review fixture','challenges':[{'type':'test','risk':'R-01','challenge':'Check approval','evidence':'the source document' if self.calls==1 else 'CPR-16; T-01.2','ask':'Inspect approval.'}]},{'role':role,'completed':True,'response_id':'fixture'}
    reviewer=Reviewer();team=LiveTeam(out.parent,ROOT,reviewer,lambda *args:None)
    result=team.challenge('Review current plan','Current evidence',maximum=8)
    assert reviewer.calls==2 and result['challenges'][0]['evidence']=='CPR-16; T-01.2'


def test_planner_retry_preserves_its_latest_rejected_revision(tmp_path):
    from webapp.live import LiveTeam
    out=tmp_path/'workspace/outputs';out.mkdir(parents=True)
    class RevisingPlanner:
        calls=0
        def generate_json(self,role,instructions,context):
            self.calls+=1
            if self.calls==2:
                assert 'new approval evidence retained' in context
                assert 'actual numeric-prose failure' in context
                assert 'old unrelated failure' not in context
            plan=json.loads((ROOT/'outputs/audit-plan.json').read_text())
            plan['memo']['purpose']=['new approval evidence retained' if self.calls==1 else 'new approval evidence retained and corrected']
            return {'plan':plan,'responses':[{'id':1,'decision':'accepted','explanation':'Updated the evidence request.'}]},{'role':role,'completed':True,'response_id':'fixture'}
    calls=[]
    def validator(work,*args):
        calls.append(args)
        if len(calls)==1:
            (work.parent/'execution.log').write_text('\n$ old-command\nold unrelated failure\n$ current-command\nactual numeric-prose failure\n')
            raise RuntimeError('rejected fixture')
    provider=RevisingPlanner();team=LiveTeam(out.parent,ROOT,provider,validator)
    team.respond('source context','older pack','Revise the plan',[{'id':1,'type':'test'}])
    assert provider.calls==2
    assert 'corrected' in (out/'audit-plan.json').read_text()


def test_model_sample_summary_uses_every_selected_row(tmp_path):
    from webapp.live import LiveTeam
    out=tmp_path/'workspace/outputs';(out/'samples').mkdir(parents=True)
    (out/'audit-plan.json').write_text('{}');(out/'planning-memo.md').write_text('# Memo')
    (out/'pack-figures.json').write_text('{}')
    (out/'samples/T-01.1.csv').write_text('row_id,amount\na,10.25\nb,20.50\na,10.25\nc,999.99\n')
    text=LiveTeam(out.parent,ROOT,FixtureProvider(),None).current_pack()
    result=json.loads(text.split('cite the test ID):\n',1)[1])['T-01.1']
    assert result['payment_occurrences']==4 and result['unique_payments']==3
    assert result['min_amount_gbp']=='10.25' and result['max_amount_gbp']=='999.99'
    assert result['example_row_ids']==['a','b','a']


def test_empty_test_procedure_is_repaired_before_builder_or_peer_review(tmp_path):
    from webapp.live import LiveTeam
    out=tmp_path/'workspace/outputs';out.mkdir(parents=True)
    class MissingProcedure(FixtureProvider):
        calls=0
        def generate_json(self,role,instructions,context):
            self.calls+=1
            plan=json.loads((ROOT/'outputs/audit-plan.json').read_text())
            if self.calls==1:plan['risks'][0]['tests'][0].pop('step')
            else:assert 'missing step text' in context
            return plan,{'role':role,'completed':True,'response_id':'fixture'}
    provider=MissingProcedure();commands=[]
    team=LiveTeam(out.parent,ROOT,provider,lambda *args:commands.append(args))
    plan=team.validated('planner','build','evidence','audit-plan.json',('fixture-validator',))
    assert provider.calls==2 and len(commands)==1
    assert plan['risks'][0]['tests'][0]['step']


def test_risk_repair_diagnostics_identify_literal_tokens_without_flagging_citations():
    from webapp.live import risk_prose_diagnostics
    risk={'id':'R-01','title':'Approval evidence','risk':'Indicator [history:AUD-15]',
        'proposed_focus':'Check S.151 approval.',
        'evidence':['{{$.population.rows_after_exclusions}} rows [metric:$.population.rows_after_exclusions]',
                    'AUD-15 used the 25000 threshold.']}
    errors=risk_prose_diagnostics({'risks':[risk]})
    assert len(errors)==2
    assert any('S.151' in x and 'proposed_focus' in x for x in errors)
    assert any('AUD-15' in x and '25000' in x for x in errors)
    assert not any('evidence[0]' in x for x in errors)


def test_risk_context_lists_exact_scalar_paths_with_bracketed_indices():
    from webapp.live import LiveTeam
    text=LiveTeam(ROOT,ROOT,FixtureProvider(),None).inputs()
    lookup=json.loads(text.split('list indices use brackets):\n',1)[1])
    analytics=json.loads((ROOT/'outputs/analytics.json').read_text())
    assert lookup['$.population.total_gbp']==analytics['population']['total_gbp']
    assert any('by_tag[' in key for key in lookup)
    assert all(isinstance(value,(int,float,bool)) for value in lookup.values())
    assert not any('top20' in key or 'row_ids' in key for key in lookup)
