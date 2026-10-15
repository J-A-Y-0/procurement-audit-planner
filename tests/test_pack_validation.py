"""Small fictional approvals exercise pack validation without approving real risks."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / '.claude/skills/audit-program/build_pack.py'


def inputs(tmp_path):
    rules = {'rules': [{'rule_id': f'CPR-{n:02}', 'clause': str(n)} for n in (1, 2)]}
    ratings = {'risks': [{'id': f'R-{n:02}', 'recommend_in_scope': True} for n in (1, 2)]}
    plan = {'generated_at': '2026-10-14', 'memo': {
        'purpose': ['Fictional fixture only.'], 'background': ['Controlled inputs.'],
        'approach': ['Inspect the stated controls.'], 'limitations': ['Not a real audit approval.']},
        'risks': [], 'rules_not_tested': []}
    for n in (1, 2):
        plan['risks'].append({'id': f'R-{n:02}', 'objective': 'Verify the control.',
            'controls': [{'id': f'C-{n:02}.1', 'control': 'Keep approval records.', 'cites': [f'rule:CPR-{n:02}']}],
            'tests': [{'id': f'T-{n:02}.1', 'control': f'C-{n:02}.1', 'step': 'Inspect the record.',
                       'evidence': 'Approval record', 'cites': [f'rule:CPR-{n:02}'],
                       'sample': {'kind': 'none', 'note': 'Document test.'}, 'pbc': ['Approval record']}],
        })
    for name, value in [('rules.json', rules), ('analytics.json', {}), ('ratings.json', ratings), ('plan.json', plan)]:
        (tmp_path / name).write_text(json.dumps(value))
    (tmp_path / 'register.md').write_text(
        '# Fixture register\n*Revision 1, following auditor comments dated 2026-10-14.*\n\n## Summary\n'
        '| ID | Risk | L | I | Score | Matrix | Band | Focus | Scope |\n'
        '| R-01 | Example one | 2 | 2 | 4 | Moderate | Moderate | Records | in |\n'
        '| R-02 | Example two | 2 | 2 | 4 | Moderate | Moderate | Records | in |\n')
    (tmp_path / 'comments.md').write_text(
        '# Fictional test approvals\nReviewer: Test fixture\nDate: 2026-10-14\n'
        '| R-01 | Example one | 2 x 2 | in | approve | Test only |\n'
        '| R-02 | Example two | 2 x 2 | in | approve | Test only |\n')
    full = tmp_path / 'full'
    full.mkdir()
    (full / 'spend-clean.csv').write_text('row_id,Supplier name,Net amount\nexample.xlsx:2,Fixture supplier,700\n')
    seal_fixture(tmp_path)
    return plan


def seal_fixture(tmp_path):
    """Fictional trusted-validator boundary for pack unit tests; never real approval."""
    (tmp_path/'history.json').write_text('{}')
    (tmp_path/'risk-baseline.json').write_text((tmp_path/'ratings.json').read_text())
    paths={'rules':'rules.json','analytics':'analytics.json','history':'history.json',
           'ratings':'ratings.json','register':'register.md','comments':'comments.md','baseline':'risk-baseline.json'}
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    method=ROOT/'.claude/skills/risk-assessment'
    state={'validated':True,'all_decided':True,'revision':1,
           'validator_sha256':digest(method/'build_register.py'),'method_sha256':digest(method/'SKILL.md'),
           'files':{k:{'path':v,'sha256':digest(tmp_path/v)} for k,v in paths.items()}}
    (tmp_path/'risk-approval-state.json').write_text(json.dumps(state))


def run_builder(tmp_path):
    return subprocess.run([sys.executable, str(BUILDER), str(tmp_path / 'plan.json'),
        '--rules', str(tmp_path / 'rules.json'), '--analytics', str(tmp_path / 'analytics.json'),
        '--ratings', str(tmp_path / 'ratings.json'), '--register', str(tmp_path / 'register.md'),
        '--comments', str(tmp_path / 'comments.md'), '--full', str(tmp_path / 'full'),
        '--out-dir', str(tmp_path / 'out')], capture_output=True, text=True)


def test_valid_two_risk_fixture_renders(tmp_path):
    inputs(tmp_path)
    result = run_builder(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '## R-01:' in (tmp_path / 'out/audit-program.md').read_text()
    assert '## R-02:' in (tmp_path / 'out/audit-program.md').read_text()


@pytest.mark.parametrize('error', ['missing_risk', 'uncited_control', 'unaccounted_rule'])
def test_invalid_plan_is_rejected(tmp_path, error):
    plan = inputs(tmp_path)
    if error == 'missing_risk':
        plan['risks'].pop()
    elif error == 'uncited_control':
        plan['risks'][0]['controls'][0]['cites'] = []
    else:
        rules = json.loads((tmp_path / 'rules.json').read_text())
        rules['rules'].append({'rule_id': 'CPR-03', 'clause': '3'})
        (tmp_path / 'rules.json').write_text(json.dumps(rules))
        seal_fixture(tmp_path)
    (tmp_path / 'plan.json').write_text(json.dumps(plan))
    result = run_builder(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'FAIL ' in result.stdout


def test_failed_rebuild_preserves_the_last_valid_pack(tmp_path):
    plan = inputs(tmp_path)
    result = run_builder(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    before = {p.name: p.read_bytes() for p in (tmp_path / 'out').glob('*.md')}
    plan['risks'].pop()
    (tmp_path / 'plan.json').write_text(json.dumps(plan))
    result = run_builder(tmp_path)
    assert result.returncode == 1
    after = {p.name: p.read_bytes() for p in (tmp_path / 'out').glob('*.md')}
    assert after == before, 'A failed build must not replace a previously valid audit pack.'


@pytest.mark.parametrize('error', ['bad_control_citation','history_only_control','unknown_inline_metric',
                                  'unknown_inline_rule','traversal_id','duplicate_test_id','literal_small_count',
                                  'bad_owner','bad_pbc','bad_sample_note','bad_exclusion_reason'])
def test_pack_rejects_unresolved_citations_and_unsafe_ids(tmp_path,error):
    plan=inputs(tmp_path)
    if error=='bad_control_citation':plan['risks'][0]['controls'][0]['cites']=['not-a-citation']
    elif error=='history_only_control':plan['risks'][0]['controls'][0]['cites']=['history:DOES-NOT-EXIST']
    elif error=='unknown_inline_metric':plan['memo']['background']=['Evidence [metric:$.missing].']
    elif error=='unknown_inline_rule':plan['risks'][0]['tests'][0]['step']='Check [rule:CPR-999].'
    elif error=='traversal_id':
        plan['risks'][0]['tests'][0].update(id='../../escaped',sample={'kind':'rows','source':'spend-clean.csv','n':1})
    elif error=='duplicate_test_id':plan['risks'][1]['tests'][0]['id']=plan['risks'][0]['tests'][0]['id']
    elif error=='bad_owner':plan['risks'][0]['controls'][0]['owner']='Owner [rule:CPR-999].'
    elif error=='bad_pbc':plan['risks'][0]['tests'][0]['pbc']=['Request [rule:CPR-999].']
    elif error=='bad_sample_note':plan['risks'][0]['tests'][0]['sample']['note']='Evidence [metric:$.does_not_exist].'
    elif error=='bad_exclusion_reason':plan['rules_not_tested']=[{'rule_ids':['CPR-01'],'reason':'Reason [rule:CPR-999].'}]
    else:plan['memo']['background']=['There are 18 payments.']
    (tmp_path/'plan.json').write_text(json.dumps(plan))
    result=run_builder(tmp_path)
    assert result.returncode==1,result.stdout+result.stderr
    assert not (tmp_path/'escaped.csv').exists()
    assert not (tmp_path/'out/planning-memo.md').exists()


def test_gate_rejects_changed_decision_after_a_successful_revision(tmp_path):
    inputs(tmp_path)
    comments=tmp_path/'comments.md'
    comments.write_text(comments.read_text().replace('| approve | Test only |','| amend | {"recommend_in_scope": false} |',1))
    result=run_builder(tmp_path)
    assert result.returncode==1 and 'changed' in result.stdout
