import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_seven_selfchecks_are_executed_not_just_six():
    result = subprocess.run([str(ROOT / '.venv/bin/python'), 'scripts/selfcheck.py'],
                            cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    for name in ('threshold_clustering', 'split_purchases', 'high_value_suppliers',
                 'off_contract', 'duplicates', 'expired_notice_spend', 'spend_vs_award'):
        assert f'PASS {name}:' in result.stdout
