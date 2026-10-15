"""Adversarial examples for requirement boundaries missed by initial self-checks."""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyse
import clean


def payments(amounts, dates=None):
    dates = dates or ['2026-05-01'] * len(amounts)
    return pd.DataFrame([{'supplier_norm': 'FIXTURE', 'Supplier name': 'Fixture Ltd',
        'Net amount': value, 'tag': 'general_procurement', 'Service': 'Finance',
        'Narrative': 'IT', 'Date': d + 'T10:00:00.000', 'pay_date': d,
        'row_id': f'fixture.xlsx:{i+2}'} for i, (value, d) in enumerate(zip(amounts, dates))])


def test_full_threshold_list_contains_all_flags_and_top20_has_row_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(analyse, 'FULL', tmp_path)
    data = payments([950] * 25)
    result = analyse.threshold_clustering(data, [{'value': 1000, 'inclusive': True,
        'rule_ids': ['X'], 'competition_triggering': True}], [])
    assert len(pd.read_csv(tmp_path / 'threshold_clustering_full.csv')) == 25
    assert len(result['1000']['top20']) == 20
    assert result['1000']['top20'][0]['row_id'].startswith('fixture.xlsx:')


def test_exclusive_threshold_comparator_does_not_overlap_lower_band(tmp_path, monkeypatch):
    monkeypatch.setattr(analyse, 'FULL', tmp_path)
    result = analyse.threshold_clustering(payments([999, 1000, 1001]), [{'value': 1000,
        'inclusive': False, 'rule_ids': ['X'], 'competition_triggering': True}], [])['1000']
    assert result['band_90pct_to_threshold']['count'] == 2
    assert result['comparator_band_threshold_to_110pct']['count'] == 1


def test_duplicate_windows_never_chain_beyond_seven_days(tmp_path, monkeypatch):
    monkeypatch.setattr(analyse, 'FULL', tmp_path)
    result = analyse.duplicates(payments([600, 600, 600], ['2026-05-01', '2026-05-07', '2026-05-13']))
    assert result['different_time']['rows'] == 3
    assert result['different_time']['gbp_beyond_first_instance'] == 1200
    for group in result['different_time']['top20_groups']:
        dates = pd.to_datetime(group['dates'])
        assert (dates.max() - dates.min()).days <= 7


def test_notice_matching_does_not_classify_small_suppliers(tmp_path, monkeypatch):
    monkeypatch.setattr(analyse, 'FULL', tmp_path)
    agg = pd.DataFrame([{'supplier_norm': 'SMALL', 'supplier_name': 'Small', 'annualised_estimate': 2000,
        'total_gbp': 500, 'n_payments': 1, 'narrative': 'IT', 'service': 'Finance', 'dominant_tag': 'general_procurement'},
        {'supplier_norm': 'LARGE', 'supplier_name': 'Large', 'annualised_estimate': 30000,
        'total_gbp': 7500, 'n_payments': 1, 'narrative': 'IT', 'service': 'Finance', 'dominant_tag': 'general_procurement'}])
    notices = pd.DataFrame([{'supplier_norm': 'ELSE', 'active': True}])
    result, _ = analyse.off_contract(agg, notices, True, False,
        publication_threshold={'value': 25000, 'inclusive': True, 'rule_ids': ['PUB']})
    assert sum(v['count'] for v in result['counts_by_match_class']) == 1
    assert result['parameters']['publication_threshold'] == 25000


def test_award_comparison_requires_unambiguous_active_notice(tmp_path, monkeypatch):
    monkeypatch.setattr(analyse, 'FULL', tmp_path)
    agg = pd.DataFrame([{'supplier_norm': 'FIXTURE', 'supplier_name': 'Fixture', 'total_gbp': 2000}])
    notices = pd.DataFrame([{'supplier_norm': 'FIXTURE', 'notice_id': str(i), 'suppliers_on_notice': 1,
        'active': True, 'awarded_value': 1000, 'contract_start': '2025-01-01', 'contract_end': '2027-01-01'} for i in range(2)])
    result = analyse.spend_vs_award(agg, notices, 3, {'rules': []})
    assert result['count'] == 0
    assert result['excluded_multiple_active_notice_suppliers'] == 1


def test_invalid_nonblank_notice_date_stops_instead_of_becoming_open_ended(tmp_path, monkeypatch):
    (tmp_path / 'data').mkdir()
    raw = pd.read_csv(ROOT / 'data/contracts.csv').head(1)
    raw = pd.concat([raw] * 20, ignore_index=True)
    raw['Organisation Name'] = 'West Berkshire Council'
    raw['Contract end date'] = 'not-a-date'
    raw.to_csv(tmp_path / 'data/contracts.csv', index=False)
    monkeypatch.setattr(clean, 'ROOT', tmp_path)
    monkeypatch.setattr(clean, 'OUT', tmp_path)
    with pytest.raises(ValueError, match='date'):
        clean.load_contracts(date(2026, 5, 1))


def test_actual_off_contract_population_reconciles_to_publication_eligible_suppliers():
    analytics = json.loads((ROOT / 'outputs/analytics.json').read_text())
    suppliers = pd.read_csv(ROOT / 'outputs/analytics-full/high_value_suppliers_all.csv')
    rules = json.loads((ROOT / 'outputs/rules.json').read_text())
    threshold = min(r['threshold_low'] for r in rules['rules'] if 'publish a contract notice' in r['required_action'])
    eligible = suppliers[suppliers.annualised_estimate >= threshold]
    assert sum(r['count'] for r in analytics['tests']['off_contract']['counts_by_match_class']) == len(eligible)
