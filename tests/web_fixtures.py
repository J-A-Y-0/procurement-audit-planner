"""Synthetic provider responses for offline harness tests only."""
import json,time
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]

def wait(client, rid, target):
    for _ in range(300):
        run = client.get('/api/runs/' + rid).json()
        if run['status'] == target:
            return run
        assert run['status'] not in ('failed', 'requires_model'), run
        time.sleep(.1)
    pytest.fail(str(run))


class FixtureProvider:
    model='fixture-only'
    def __init__(self):self.roles=[]
    def generate_json(self,role,instructions,context):
        self.roles.append(role)
        if role=='risk-assessor':
            value=json.loads((ROOT/'outputs/risk-ratings.json').read_text());value.pop('revision',None)
        elif role=='planner':
            value=json.loads((ROOT/'outputs/audit-plan.json').read_text())
            if 'FILE risk-ratings.json\n' in context:
                raw=context.split('FILE risk-ratings.json\n',1)[1]
                ratings=json.JSONDecoder().raw_decode(raw)[0]
                ids={r['id'] for r in ratings['risks'] if r['recommend_in_scope']}
                value['risks']=[r for r in value['risks'] if r['id'] in ids]
                import re
                corpus=json.dumps([ratings['risks'],value['risks']])
                cited=set(re.findall(r'\[rule:(CPR-\d+)\]',corpus))|set(re.findall(r'"rule:(CPR-\d+)"',corpus))
                previous={rid:g['reason'] for g in value['rules_not_tested'] for rid in g['rule_ids']}
                rules=json.loads((ROOT/'outputs/rules.json').read_text())
                value['rules_not_tested']=[{'rule_ids':[r['rule_id']],'reason':previous.get(r['rule_id'],'Related risk excluded by the test scope; no separate fieldwork planned.')} for r in rules['rules'] if r['rule_id'] not in cited]
        elif role=='challenger':value={'summary':'No actionable findings in this test fixture.','challenges':[]}
        elif role=='qa-reviewer':value={'verdict':'ready','summary':'Deterministic checks pass in fixture.','issues':[]}
        else:raise AssertionError(role)
        return value,{'role':role,'model':self.model,'completed':True,'response_id':'fixture-'+str(len(self.roles))}
