"""Exercise approval and sampling boundaries using independent small fixtures."""
import csv
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_pack', ROOT / '.claude/skills/audit-program/build_pack.py')
pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack)


def test_blank_decision_and_unrevised_register_block_scope():
    failures = []
    pack.scope_check({'R-01': {'title': 'Example'}}, None,
                     {'rows': {'R-01': {'decision': '', 'comment': ''}}},
                     {'risks': [{'id': 'R-01'}]}, failures)
    assert any('no decision' in f for f in failures)
    assert any('not a revision' in f for f in failures)


def test_rejected_risk_still_in_register_blocks_scope():
    failures = []
    pack.scope_check({'R-01': {'title': 'Example'}}, 1,
                     {'rows': {'R-01': {'title': 'Example', 'decision': 'reject', 'comment': 'Separate review'}}},
                     {'risks': [{'id': 'R-01'}]}, failures)
    assert any('rejected but is still in the register' in f for f in failures)


def test_only_explicitly_approved_scope_passes():
    failures = []
    approved, excluded = pack.scope_check(
        {'R-01': {'title': 'Included'}}, 1,
        {'rows': {'R-01': {'decision': 'approve', 'comment': ''}}},
        {'risks': [{'id': 'R-01', 'recommend_in_scope': True}]}, failures)
    assert failures == []
    assert list(approved) == ['R-01']
    assert excluded == {}


def write_rows(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_sample_selects_largest_eligible_rows_and_is_repeatable(tmp_path):
    write_rows(tmp_path / 'flags.csv', [
        {'row_id': 'example.xlsx:2', 'amount': 700, 'tag': 'general'},
        {'row_id': 'example.xlsx:3', 'amount': 900, 'tag': 'care'},
        {'row_id': 'example.xlsx:4', 'amount': 800, 'tag': 'general'},
    ])
    spend = {f'example.xlsx:{i}': {'row_id': f'example.xlsx:{i}', 'Net amount': amount,
             'Supplier name': 'Fixture supplier', 'source_file': 'example.xlsx', 'sheet_row': i}
             for i, amount in [(2, 700), (3, 900), (4, 800)]}
    recipe = {'kind': 'rows', 'source': 'flags.csv', 'where': {'tag': 'general'},
              'order_by': 'amount', 'descending': True, 'n': 1}
    errors = []
    result, _ = pack.draw_sample(recipe, 'T-01.1', tmp_path, spend, errors)
    assert errors == []
    assert [r['row_id'] for r in result] == ['example.xlsx:4']
    again, _ = pack.draw_sample(recipe, 'T-01.1', tmp_path, spend, [])
    assert again == result


def test_sample_rejects_row_absent_from_clean_population(tmp_path):
    write_rows(tmp_path / 'flags.csv', [{'row_id': 'missing.xlsx:999', 'amount': 700}])
    errors = []
    result, _ = pack.draw_sample({'kind': 'rows', 'source': 'flags.csv', 'n': 1},
                                 'T-01.1', tmp_path, {}, errors)
    assert result == []
    assert any('not found in spend-clean.csv' in f for f in errors)


def test_sample_source_cannot_escape_the_analytics_directory(tmp_path):
    full = tmp_path / 'full'
    full.mkdir()
    write_rows(tmp_path / 'outside.csv', [{'row_id': 'example.xlsx:2'}])
    errors = []
    rows, _ = pack.draw_sample({'kind': 'rows', 'source': '../outside.csv'},
                               'T-01.1', full, {'example.xlsx:2': {'row_id': 'example.xlsx:2'}}, errors)
    assert rows == []
    assert any('outside' in e for e in errors)


@pytest.mark.parametrize('filename', ['split_purchases_windows.csv', 'duplicates.csv'])
def test_group_sampling_reads_actual_analyst_output_lists(filename):
    full = ROOT / 'outputs/analytics-full'
    with (full / 'spend-clean.csv').open(newline='') as stream:
        spend = {r['row_id']:r for r in csv.DictReader(stream)}
    errors = []
    rows, _ = pack.draw_sample({'kind':'groups', 'source':filename, 'n':1, 'per_group_n':2},
                               'T-01.1', full, spend, errors)
    assert not errors
    assert len(rows) == 2 and all(r['row_id'] in spend for r in rows)


@pytest.mark.parametrize('path', ['$.value[abc]', '$garbage', '$.value[0]trailing'])
def test_metric_paths_must_be_fully_valid(path):
    found, _ = pack.jpath({'value': 700}, path)
    assert found is False
