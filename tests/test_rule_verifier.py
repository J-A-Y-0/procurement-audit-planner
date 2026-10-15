"""Run the guide verifier against controlled fixtures, including planted errors."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / '.claude/skills/extract-rules/verify_quotes.py'


def fixture():
    return {
        'source': {'file': 'data/contract-rules.pdf'}, 'parameters': {},
        'notes': [], 'excluded': [], 'rules': [{
            'rule_id': 'CPR-01', 'clause': '4.2', 'page': 3,
            'type': 'required-action', 'scope': 'all',
            'condition': 'Entering a contract', 'threshold_low': None,
            'threshold_low_inclusive': None, 'threshold_high': None,
            'threshold_high_inclusive': None,
            'required_action': 'Confirm approved budgetary provision.',
            'approver': None, 'evidence_source': 'council-records',
            'verbatim_quote': 'No contract shall be entered into unless it is in accordance with an existing budgetary provision within the Budget approved by the Council.',
        }],
    }


def run_check(tmp_path, data):
    source = tmp_path / 'rules.json'
    source.write_text(json.dumps(data))
    return subprocess.run(
        [sys.executable, str(VERIFIER), str(source), str(ROOT / 'data/contract-rules.pdf')],
        capture_output=True, text=True,
    )


def test_accepts_an_actual_quote_on_its_actual_page(tmp_path):
    result = run_check(tmp_path, fixture())
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ALL CHECKS PASSED' in result.stdout


@pytest.mark.parametrize('error', ['wrong_quote', 'wrong_page', 'unknown_parameter', 'missing_field', 'wrong_id'])
def test_rejects_planted_errors(tmp_path, error):
    data = fixture()
    rule = data['rules'][0]
    if error == 'wrong_quote':
        rule['verbatim_quote'] = rule['verbatim_quote'].replace('No contract', 'Every contract')
    elif error == 'wrong_page':
        rule['page'] = 2
    elif error == 'unknown_parameter':
        rule['threshold_high_ref'] = 'UNDECLARED_PARAMETER'
    elif error == 'missing_field':
        del rule['required_action']
    else:
        rule['rule_id'] = 'CPR-02'
    result = run_check(tmp_path, data)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'FAIL ' in result.stdout
