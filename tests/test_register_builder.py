"""Decision and citation controls; fictional fixtures are never real approval."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'register_builder', ROOT / '.claude/skills/risk-assessment/build_register.py')


@pytest.fixture
def builder():
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


@pytest.fixture
def case(tmp_path):
    out = tmp_path / 'outputs'
    out.mkdir()
    history = json.loads((ROOT / 'outputs/history.json').read_text())
    rules = json.loads((ROOT / 'outputs/rules.json').read_text())
    analytics = {'population': {'rows_after_exclusions': 4, 'total_gbp': 12000}}
    risk = {
        'id': 'R-01', 'title': 'Fictional budget evidence gap',
        'risk': 'Budget authority may not be evidenced.',
        'likelihood': {'base_score': 2, 'score': 2,
                       'justification': 'The required budget approval needs inspection [rule:CPR-01].'},
        'impact': {'score': 3,
                   'justification': 'A compliance consequence is a scenario, not an observed loss [history:RT-02].'},
        'evidence': ['The fictional population contains {{$.population.rows_after_exclusions}} rows [metric:$.population.rows_after_exclusions].'],
        'proposed_focus': 'Obtain and inspect approval evidence.',
        'recommend_in_scope': True, 'sample_source': ''}
    ratings = {'generated_at': '2026-10-15', 'risks': [risk], 'excluded': []}
    for name, value in [('rules', rules), ('history', history), ('analytics', analytics), ('risk-ratings', ratings)]:
        (out / (name + '.json')).write_text(json.dumps(value))
    return tmp_path, ratings


def save(root, ratings):
    (root / 'outputs/risk-ratings.json').write_text(json.dumps(ratings))


def decide(root, decision, comment=''):
    path = root / 'outputs/auditor-comments.md'
    text = path.read_text().replace('|  |  |', f'| {decision} | {comment} |')
    path.write_text(text)


def test_good_risk_renders_council_matrix_and_blank_decision(builder, case):
    root, _ = case
    result = builder.build(root)
    assert not result['errors'] and not result['warnings']
    rendered = (root / 'outputs/risk-register.md').read_text()
    assert '| R-01 | Fictional budget evidence gap | 2 | 3 | 6 | Moderate | Moderate |' in rendered
    assert 'None recorded' in rendered and 'Figure 4' in rendered
    assert '|  |  |' in (root / 'outputs/auditor-comments.md').read_text()


def test_broken_risk_is_dropped_and_not_published(builder, case):
    root, ratings = case
    bad = copy.deepcopy(ratings['risks'][0]); bad['id'] = 'R-02'
    bad['likelihood']['justification'] = 'No actual citation.'
    ratings['risks'].append(bad); save(root, ratings)
    result = builder.build(root)
    assert result['kept_ids'] == ['R-01']
    assert any(x['id'] == 'R-02' for x in result['dropped'])
    assert result['errors'] and not (root / 'outputs/risk-register.md').exists()


@pytest.mark.parametrize('text', [
    'Missing value [metric:$.population.typo].',
    'Missing rule [rule:CPR-999].',
    'Missing history [history:NOT-AN-ID].',
    'A collection is not a scalar {{$.population}} [rule:CPR-01].'])
def test_unresolvable_citation_or_placeholder_blocks(builder, case, text):
    root, ratings = case
    ratings['risks'][0]['likelihood']['justification'] = text
    save(root, ratings)
    assert builder.build(root)['errors']


def test_repeat_uplift_requires_adverse_audit(builder, case):
    root, ratings = case
    like = ratings['risks'][0]['likelihood']
    like.update(score=3, repeat_audit_id='AUD-01')
    like['justification'] += ' Prior finding [history:AUD-01].'
    save(root, ratings)
    assert any('adverse' in e for e in builder.build(root)['errors'])
    like['repeat_audit_id'] = 'AUD-16'
    like['justification'] = like['justification'].replace('AUD-01', 'AUD-16')
    save(root, ratings)
    assert not builder.build(root)['errors']


def test_documented_array_index_history_and_metric_citations_resolve(builder, case):
    root, ratings = case
    ratings['risks'][0]['impact']['justification'] = 'A consequence scenario [history:$.scoring_method.impact_scale[2]].'
    analytics_path = root / 'outputs/analytics.json'
    analytics = json.loads(analytics_path.read_text()); analytics['items'] = [{'count': 4}]
    analytics_path.write_text(json.dumps(analytics))
    ratings['risks'][0]['evidence'] = ['{{$.items[0].count}} rows [metric:$.items[0].count].']
    save(root, ratings)
    result = builder.build(root)
    assert not result['errors'] and not result['warnings']


def test_every_placeholder_metric_is_listed_in_rendered_source_references(builder,case):
    root,ratings=case
    ratings['risks'][0]['evidence']=['Exposure {{$.population.total_gbp}} [rule:CPR-01].']
    save(root,ratings)
    assert not builder.build(root)['errors']
    assert '[metric:$.population.total_gbp] analytics.json:' in (root/'outputs/risk-register.md').read_text()


def test_literal_figures_warn_and_cannot_publish(builder, case):
    root, ratings = case
    ratings['risks'][0]['evidence'] = ['There were 4 rows [rule:CPR-01].']
    save(root, ratings)
    assert builder.build(root)['warnings']
    assert not (root / 'outputs/risk-register.md').exists()


def test_approved_risk_cannot_change_and_last_valid_register_survives(builder, case):
    root, ratings = case
    assert not builder.build(root)['errors']
    decide(root, 'approve')
    prior = (root / 'outputs/risk-register.md').read_bytes()
    ratings['risks'][0]['impact']['score'] = 4
    ratings['revision'] = {'number': 1, 'changes': []}
    save(root, ratings)
    assert any('approved' in e for e in builder.build(root)['errors'])
    assert (root / 'outputs/risk-register.md').read_bytes() == prior


def test_approve_revision_keeps_decision(builder, case):
    root, ratings = case
    builder.build(root); decide(root, 'approve', 'Fictional fixture approval')
    ratings['revision'] = {'number': 1, 'changes': []}; save(root, ratings)
    result = builder.build(root)
    assert not result['errors']
    assert '*Revision 1, following auditor comments' in (root / 'outputs/risk-register.md').read_text()
    assert '| approve | Fictional fixture approval |' in (root / 'outputs/auditor-comments.md').read_text()


def test_amendment_requires_exact_structured_changes(builder, case):
    root, ratings = case
    builder.build(root)
    decide(root, 'amend', '{"recommend_in_scope": false}')
    ratings['revision'] = {'number': 1, 'changes': [{'id': 'R-01', 'action': 'amended'}]}
    save(root, ratings)
    assert builder.build(root)['errors']
    ratings['risks'][0]['recommend_in_scope'] = False; save(root, ratings)
    assert not builder.build(root)['errors']
    ratings['risks'][0]['title'] = 'Unrequested change'; save(root, ratings)
    assert builder.build(root)['errors']


def test_rejection_requires_removal_and_reason(builder, case):
    root, ratings = case
    builder.build(root); decide(root, 'reject', 'Fictional exclusion reason')
    ratings['revision'] = {'number': 1, 'changes': [{'id': 'R-01', 'action': 'rejected'}]}
    save(root, ratings)
    assert builder.build(root)['errors']
    ratings['risks'] = []; ratings['excluded'] = [{'id': 'R-01', 'reason': 'Fictional exclusion reason'}]
    save(root, ratings)
    assert not builder.build(root)['errors']
    assert not builder.build(root)['errors'], 'A validated all-rejected revision must rebuild identically.'


def test_score_only_amendment_without_new_cited_justification_blocks(builder, case):
    root, ratings = case
    builder.build(root); decide(root, 'amend', '{"impact.score": 5}')
    ratings['risks'][0]['impact']['score'] = 5
    ratings['revision'] = {'number':1,'changes':[{'id':'R-01','action':'amended'}]}
    save(root, ratings)
    assert any('justification' in e for e in builder.build(root)['errors'])


def test_approval_can_follow_a_validated_scope_amendment(builder, case):
    root, ratings = case
    builder.build(root); decide(root, 'amend', '{"recommend_in_scope": false}')
    ratings['risks'][0]['recommend_in_scope'] = False
    ratings['revision'] = {'number':1,'changes':[{'id':'R-01','action':'amended'}]}
    save(root, ratings); assert not builder.build(root)['errors']
    comments = root/'outputs/auditor-comments.md'
    comments.write_text(comments.read_text().replace('| amend | {"recommend_in_scope": false} |', '| approve | Reviewed amended scope |'))
    ratings['revision'] = {'number':2,'changes':[]};save(root,ratings)
    assert not builder.build(root)['errors']


def test_gate_snapshot_rejects_later_comment_or_input_edits(builder, case):
    root, ratings = case
    builder.build(root);decide(root,'approve')
    ratings['revision']={'number':1,'changes':[]};save(root,ratings)
    assert not builder.build(root)['errors']
    assert not builder.verify_approval_state(root/'outputs/risk-approval-state.json')
    comments=root/'outputs/auditor-comments.md';comments.write_text(comments.read_text()+'\nNew instruction\n')
    assert any('changed' in e for e in builder.verify_approval_state(root/'outputs/risk-approval-state.json'))


def test_partial_human_decisions_can_be_revised_but_do_not_close_planning_gate(builder,case):
    root,ratings=case
    second=copy.deepcopy(ratings['risks'][0]);second['id']='R-02';second['title']='Second fictional risk'
    ratings['risks'].append(second);save(root,ratings)
    assert not builder.build(root)['errors']
    path=root/'outputs/auditor-comments.md'
    path.write_text(path.read_text().replace('|  |  |','| approve | Reviewed first risk |',1))
    ratings['revision']={'number':1,'changes':[]};save(root,ratings)
    assert not builder.build(root)['errors']
    assert 'R-02: undecided' in (root/'outputs/risk-register.md').read_text()
    assert builder.verify_approval_state(root/'outputs/risk-approval-state.json')
