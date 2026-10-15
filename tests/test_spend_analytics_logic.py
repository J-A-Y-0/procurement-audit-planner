"""Small-fixture tests for the spend-analyst clean.py / analyse.py logic."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import clean as clean_mod  # noqa: E402
import analyse as analyse_mod  # noqa: E402


# --- clean.py: tagging ---

@pytest.mark.parametrize(('service', 'narrative', 'expected'), [
    ('Adult Social Care', 'Private Contractors', 'care_or_education_placement'),
    ("Children's Social Care", 'Other agencies', 'care_or_education_placement'),
    ('Education & SEND', 'Voluntary Associations', 'care_or_education_placement'),
    ('Environment', 'Private Contractors', 'general_procurement'),  # wrong service prefix
    ('Adult Social Care', 'Grants to voluntary bodies', 'grant'),  # GRANT wins before placement check fails anyway
    ('Finance', 'Agency & Temporary Staff', 'agency_staff'),
    ('Finance', 'Rents', 'premises_non_procurement'),
    ('Finance', 'IT', 'general_procurement'),
])
def test_tag_row_first_match_wins(service, narrative, expected):
    assert clean_mod.tag_row(service, narrative) == expected


def test_tag_row_placement_requires_both_service_prefix_and_narrative():
    # Right narrative, wrong service: must not be tagged as a placement.
    assert clean_mod.tag_row('Environment', 'Other agencies') == 'general_procurement'
    # Right service, narrative not in the placement set: falls through.
    assert clean_mod.tag_row('Adult Social Care', 'IT') == 'general_procurement'


# --- clean.py: exclusions ---

def test_classify_exclusion_redacted():
    row = {'Supplier name': 'redacted', 'Narrative': 'Private Contractors'}
    assert clean_mod.classify_exclusion(row) == 'redacted_supplier'


def test_classify_exclusion_pension():
    row = {'Supplier name': 'Some Pension Fund', 'Narrative': 'LGPS Pension deficit'}
    assert clean_mod.classify_exclusion(row) == 'pension_statutory'


def test_classify_exclusion_inter_authority_supplier_name():
    row = {'Supplier name': 'Reading Borough Council', 'Narrative': 'Joint service'}
    assert clean_mod.classify_exclusion(row) == 'inter_authority'


def test_classify_exclusion_inter_authority_exempted_by_private_contractors_narrative():
    # Narrative == 'Private Contractors' exempts an otherwise-matching supplier name.
    row = {'Supplier name': 'Some Fire Authority Services Ltd', 'Narrative': 'Private Contractors'}
    assert clean_mod.classify_exclusion(row) is None


def test_classify_exclusion_none_for_ordinary_supplier():
    row = {'Supplier name': 'Acme Builders Ltd', 'Narrative': 'Private Contractors'}
    assert clean_mod.classify_exclusion(row) is None


# --- analyse.py: threshold derivation ---

def test_build_thresholds_marks_quote_rule_as_competition_triggering():
    rules_doc = {
        'parameters': {},
        'rules': [
            {'rule_id': 'X1', 'type': 'threshold', 'threshold_low': 1000, 'threshold_low_inclusive': False,
             'threshold_high': 25000, 'threshold_high_inclusive': False,
             'required_action': 'obtain at least one quote from an appropriate source'},
            {'rule_id': 'X2', 'type': 'threshold', 'threshold_low': 500000, 'threshold_low_inclusive': False,
             'threshold_high': None, 'threshold_high_inclusive': None,
             'required_action': 'treat the contract award as a Key Decision'},
        ],
    }
    thresholds, skipped = analyse_mod.build_thresholds(rules_doc)
    by_value = {t['value']: t for t in thresholds}
    assert by_value[1000]['competition_triggering'] is True
    assert by_value[25000]['competition_triggering'] is True
    assert by_value[500000]['competition_triggering'] is False
    assert skipped == []


def test_build_thresholds_records_null_parameter_refs_as_skipped():
    rules_doc = {
        'parameters': {'THRESHOLD_APPLICABLE': {'value': None}},
        'rules': [
            {'rule_id': 'Y1', 'type': 'threshold', 'threshold_low': None, 'threshold_low_inclusive': False,
             'threshold_high': None, 'threshold_high_inclusive': None,
             'threshold_low_ref': 'THRESHOLD_APPLICABLE',
             'required_action': 'run a full competitive tender'},
        ],
    }
    thresholds, skipped = analyse_mod.build_thresholds(rules_doc)
    assert thresholds == []
    assert skipped == [{'rule_id': 'Y1', 'parameter': 'THRESHOLD_APPLICABLE',
                         'reason': 'THRESHOLD_APPLICABLE is null in rules.json parameters'}]


# --- analyse.py: supplier matching ---

def test_match_supplier_exact():
    cls, candidate, rule = analyse_mod.match_supplier('ACME BUILDERS', {'ACME BUILDERS', 'OTHER CO'}, {}, {})
    assert cls == 'exact'
    assert candidate == 'ACME BUILDERS'


def test_match_supplier_near_ratio():
    cls, candidate, rule = analyse_mod.match_supplier('ACME BUILDER', {'ACME BUILDERS'}, {}, {})
    assert cls == 'near_ratio'


def test_match_supplier_near_contain_multi_token():
    spend_counts = {'SOUTHERN': 1, 'COACH': 1, 'LINES': 1}
    notice_counts = {'SOUTHERN': 1, 'COACH': 1, 'LINES': 1}
    cls, candidate, rule = analyse_mod.match_supplier(
        'SOUTHERN COACH LINES AND ASSOCIATES', {'SOUTHERN COACH LINES'}, spend_counts, notice_counts)
    assert cls == 'near_contain'


def test_match_supplier_none_when_tokens_differ():
    cls, candidate, rule = analyse_mod.match_supplier('ZEBRA WIDGETS', {'ACME BUILDERS'}, {}, {})
    assert cls == 'none'
    assert candidate is None


def test_distinctive_tokens_drops_generic_words_and_short_tokens():
    tokens = analyse_mod.distinctive_tokens('THE ACME CARE GROUP OF A B')
    assert tokens == {'ACME'}
