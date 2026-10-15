import json
import httpx
import pytest
from webapp.budget import ApiBudget,BudgetError
from webapp.provider import AnthropicProvider,ProviderError
from tests.test_provider import complete

def test_reservation_blocks_overspend_and_survives_restart(tmp_path):
    p=tmp_path/'budget.json';b=ApiBudget(p,.022)
    token=b.reserve('claude-haiku-5-5',50000,18000)
    with pytest.raises(BudgetError,match='budget cannot cover'):
        ApiBudget(p,.022).reserve('claude-haiku-5-5',50000,18000)
    actual=b.settle(token,{'input_tokens':50000,'output_tokens':1000})
    assert actual==.0055
    assert ApiBudget(p,.022).reserve('claude-haiku-5-5',50000,18000)

def test_high_context_tariff_and_expensive_model_are_blocked(tmp_path):
    b=ApiBudget(tmp_path/'budget.json',.03)
    with pytest.raises(BudgetError):b.reserve('claude-haiku-5-5',100001,18000)
    with pytest.raises(BudgetError):b.reserve('claude-sonnet-5-5',10,10)

def test_budget_denial_prevents_billed_generation(tmp_path):
    paths=[]
    def handle(r):
        paths.append(r.url.path)
        assert r.url.path=='/v1/messages/count_tokens'
        return httpx.Response(200,json={'input_tokens':100000})
    provider=AnthropicProvider('test','claude-haiku-5-5',transport=httpx.MockTransport(handle),budget=ApiBudget(tmp_path/'b.json',.001))
    with pytest.raises(ProviderError,match='budget cannot cover'):provider.generate_json('qa-reviewer','x','y')
    assert paths==['/v1/messages/count_tokens']

def test_completed_generation_records_spend_and_failed_stream_retains_reservation(tmp_path):
    b=ApiBudget(tmp_path/'b.json',1)
    def handle(r):
        if r.url.path.endswith('count_tokens'):return httpx.Response(200,json={'input_tokens':10})
        return httpx.Response(200,text=complete())
    p=AnthropicProvider('test','claude-haiku-5-5',transport=httpx.MockTransport(handle),budget=b)
    value,receipt=p.generate_json('qa-reviewer','x','y')
    assert receipt['estimated_cost_usd']>0
    assert not b.read()['reservations']
    p.transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'input_tokens':10}) if r.url.path.endswith('count_tokens') else httpx.Response(200,text=''))
    with pytest.raises(ProviderError):p.generate_json('qa-reviewer','x','y')
    assert len(b.read()['reservations'])==1


def test_truncated_completed_stream_reports_usage_and_blocks_without_retry(tmp_path):
    b=ApiBudget(tmp_path/'b.json',1);generations=[]
    def handle(r):
        if r.url.path.endswith('count_tokens'):return httpx.Response(200,json={'input_tokens':10})
        generations.append(r)
        return httpx.Response(200,text=complete(reason='max_tokens'))
    p=AnthropicProvider('test','claude-haiku-5-5',transport=httpx.MockTransport(handle),budget=b)
    with pytest.raises(ProviderError,match='max_tokens') as caught:p.generate_json('planner','x','y')
    assert len(generations)==1 and not b.read()['reservations']
    assert caught.value.receipt['completed'] is False
    assert caught.value.receipt['estimated_cost_usd']>0
