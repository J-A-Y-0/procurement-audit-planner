import json
import httpx
import pytest


def sse(*events):
    return '\n\n'.join('data: '+json.dumps(e) for e in events)+'\n\n'


def complete(text='{"verdict":"ready","summary":"Checked","issues":[]}',reason='end_turn'):
    return sse({'type':'message_start','message':{'id':'msg_test','model':'claude-test','usage':{'input_tokens':10}}},
       {'type':'content_block_delta','delta':{'type':'text_delta','text':text}},
       {'type':'message_delta','delta':{'stop_reason':reason},'usage':{'output_tokens':5}},
       {'type':'message_stop'})


def planner_wire(plan):
    plan=json.loads(json.dumps(plan))
    for risk in plan['risks']:
        for control in risk['controls']:control.setdefault('owner','')
        for test in risk['tests']:test['sample_json']=json.dumps(test.pop('sample'))
    return {'plan':plan,'responses':[]}


def test_anthropic_completed_stream_and_server_side_key():
    from webapp.provider import AnthropicProvider
    requests=[]
    def handle(request):
        requests.append(request)
        return httpx.Response(200,text=complete())
    p=AnthropicProvider('secret-test','claude-test',transport=httpx.MockTransport(handle))
    result,receipt=p.generate_json('qa-reviewer','Return JSON','Read the evidence')
    assert result=={'verdict':'ready','summary':'Checked','issues':[]}
    assert receipt['completed'] is True and receipt['response_id']=='msg_test'
    assert receipt['provider']=='anthropic'
    assert 'secret-test' not in json.dumps(receipt)
    request=requests[0];body=json.loads(request.content)
    assert str(request.url)=='https://api.anthropic.com/v1/messages'
    assert request.headers['x-api-key']=='secret-test'
    assert request.headers['anthropic-version']=='2023-06-01'
    assert body['stream'] is True and body['max_tokens']==18000
    assert body['messages'][0]['role']=='user'
    assert body['model']=='claude-test' and 'system' in body
    assert body['output_config']['format']['type']=='json_schema'
    schema=body['output_config']['format']['schema']
    assert schema['additionalProperties'] is False
    assert set(schema['required'])=={'verdict','summary','issues'}


def test_parseable_wrong_contract_is_blocked_without_retry():
    from webapp.provider import AnthropicProvider,ProviderError
    requests=[]
    def handle(request):
        requests.append(request)
        return httpx.Response(200,text=complete('{"verdict":"ready"}'))
    p=AnthropicProvider('test','claude-test',transport=httpx.MockTransport(handle))
    with pytest.raises(ProviderError,match='response contract'):
        p.generate_json('qa-reviewer','Return JSON','context')
    assert len(requests)==1


def test_planner_transport_restores_filters_and_challenge_response_shape():
    from pathlib import Path
    from webapp.contracts import response_contract,restore_artifact
    from jsonschema import Draft202012Validator
    plan=json.loads((Path(__file__).resolve().parents[1]/'outputs/audit-plan.json').read_text())
    original=json.loads(json.dumps(plan))
    wire=planner_wire(plan)
    schema,reply=response_contract('planner','CURRENT TASK:\nWrite audit-plan.json')
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(wire)
    restored=restore_artifact('planner',wire,reply)
    for source,risk in zip(original['risks'],restored['risks']):
        for before,after in zip(source['tests'],risk['tests']):
            for key,value in before['sample'].items():assert after['sample'][key]==value
            assert before['step']==after['step']
    _,reply=response_contract('planner','CURRENT TASK:\nReturn JSON {"plan":{},"responses":[]}')
    assert reply and restore_artifact('planner',wire,reply)['plan']==restored
    assert restored==original



def test_structured_transport_runs_original_tools_and_signoff_gate(tmp_path):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from tests.web_fixtures import FixtureProvider,wait
    from webapp.main import create_app
    from webapp.provider import AnthropicProvider
    fixture=FixtureProvider()
    def handle(request):
        body=json.loads(request.content)
        fields=body['output_config']['format']['schema']['properties']
        role='planner' if 'plan' in fields else 'risk-assessor' if 'risks' in fields else 'qa-reviewer' if 'verdict' in fields else 'challenger'
        value,_=fixture.generate_json(role,body['system'],body['messages'][0]['content'])
        if role=='planner':value=planner_wire(value)
        if role=='challenger':value.update(statuses=[],additional_blockers=[])
        return httpx.Response(200,text=complete(json.dumps(value)))
    provider=AnthropicProvider('offline-only','claude-test',transport=httpx.MockTransport(handle))
    app=create_app(tmp_path/'runs',Path(__file__).resolve().parents[1],provider=provider)
    with TestClient(app) as c:
        run=c.post('/api/runs',json={'title':'Offline structured transport test'}).json()
        run=wait(c,run['id'],'awaiting_scope')
        response=c.post('/api/runs/'+run['id']+'/scope',json={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15',
            'decisions':[{'id':r['id'],'decision':'approve','in_scope':r['recommend_in_scope']} for r in run['risks']]})
        assert response.status_code==202,response.text
        run=wait(c,run['id'],'awaiting_signoff')
        assert len(run['qa'])==4 and all(q['result']=='PASS' for q in run['qa'])
        assert c.get('/api/runs/'+run['id']+'/download').status_code==409
        response=c.post('/api/runs/'+run['id']+'/signoff',json={'expected_version':run['version'],'reviewer':'Test Reviewer','date':'2026-10-15','decision':'sign_off'})
        assert response.status_code==200,response.text
        assert c.get('/api/runs/'+run['id']+'/download').status_code==200


@pytest.mark.parametrize('recipe',['not JSON','[]','{"n":1,"n":2}','{"n":NaN}'])
def test_recipe_transport_rejects_invalid_or_ambiguous_json(recipe):
    from webapp.contracts import parse_recipe
    with pytest.raises(ValueError):parse_recipe(recipe)


@pytest.mark.parametrize('body',[
    sse({'type':'content_block_delta','delta':{'type':'text_delta','text':'{"value":1}'}}),
    sse({'type':'error','error':{'type':'overloaded_error','message':'secret-test'}}),
    complete('not json'),complete(reason='max_tokens'),complete(reason='tool_use'),
])
def test_incomplete_failed_or_invalid_json_blocks(body):
    from webapp.provider import AnthropicProvider,ProviderError
    p=AnthropicProvider('secret-test','claude-test',transport=httpx.MockTransport(lambda r:httpx.Response(200,text=body)))
    with pytest.raises(ProviderError) as caught:p.generate_json('planner','Return JSON','context')
    assert 'secret-test' not in str(caught.value)


def test_provider_http_failure_has_safe_actionable_status():
    from webapp.provider import AnthropicProvider,ProviderError
    p=AnthropicProvider('secret-test','claude-test',transport=httpx.MockTransport(lambda r:httpx.Response(429,json={'error':{'message':'secret-test'}})))
    with pytest.raises(ProviderError,match='429') as caught:p.generate_json('planner','Return JSON','context')
    assert 'secret-test' not in str(caught.value)


def test_config_uses_anthropic_only(tmp_path,monkeypatch):
    from webapp.provider import configured_provider
    monkeypatch.delenv('ANTHROPIC_API_KEY',raising=False)
    monkeypatch.delenv('AUDIT_MODEL',raising=False)
    monkeypatch.setenv('OPENAI_API_KEY','must-not-be-used')
    assert configured_provider(tmp_path) is None
    (tmp_path/'.env').write_text('ANTHROPIC_API_KEY=secret-test\nAUDIT_MODEL=claude-test\n')
    assert configured_provider(tmp_path).model=='claude-test'
