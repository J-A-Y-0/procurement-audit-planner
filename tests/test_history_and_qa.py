"""Verify quote, numeric and original-workbook QA with planted errors."""
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]


def invoke(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True)


@pytest.mark.parametrize('error', [None, 'wrong_quote', 'wrong_page', 'missing_source'])
def test_history_quote_verification(tmp_path, error):
    source = 'audit-completed-work-2025-26-q3.pdf'
    item = {'source': source, 'pdf_page': 1, 'quote':
            'The overall opinion is derived from the number/significance of recommendations together with using professional judgement.'}
    doc = {k: [] for k in ['source_documents', 'gaps', 'audits', 'opinion_basis',
           'agreed_actions', 'planned_audits', 'audit_approach', 'risk_themes', 'discrepancies']}
    doc.update(generated_at='2026-10-14', scoring_method={'usable': False})
    doc['audits'] = [item]
    if error == 'wrong_quote':
        item['quote'] = item['quote'].replace('professional judgement', 'automatic approval')
    elif error == 'wrong_page':
        item['pdf_page'] = 2
    elif error == 'missing_source':
        item['source'] = 'nonexistent.pdf'
    path = tmp_path / 'history.json'
    path.write_text(json.dumps(doc))
    result = invoke(ROOT / 'scripts/verify_history.py', path, ROOT / 'data/committee')
    assert result.returncode == (1 if error else 0), result.stdout + result.stderr
    assert ('FAIL ' if error else 'ALL CHECKS PASSED') in result.stdout


def qa_fixture(tmp_path, check):
    target = tmp_path / 'scripts/checks' / check
    target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / 'scripts/checks' / check, target)
    out = tmp_path / 'outputs'
    out.mkdir()
    return target, out


def test_number_check_rejects_a_planted_unsupported_figure(tmp_path):
    script, out = qa_fixture(tmp_path, 'check_numbers.py')
    (out / 'analytics.json').write_text(json.dumps({'total': 700}))
    (out / 'rules.json').write_text(json.dumps({'rules': []}))
    for name in ['planning-memo.md', 'risk-control-matrix.md', 'audit-program.md']:
        (out / name).write_text('Verified total £700.00.\n')
    result = invoke(script)
    assert result.returncode == 0, result.stdout + result.stderr
    (out / 'planning-memo.md').write_text('Unsupported total £987,654.00.\n')
    result = invoke(script)
    assert result.returncode == 1
    assert '£987,654.00 not found' in result.stdout


@pytest.mark.parametrize('figure', ['66,778,104.78', '1,202,625.25', '2026.25', '£2026.25'])
def test_number_check_reads_complete_decimal_amounts(tmp_path, figure):
    script, out = qa_fixture(tmp_path, 'check_numbers.py')
    value = float(figure.replace('£', '').replace(',', ''))
    (out / 'analytics.json').write_text(json.dumps({'total': value}))
    for name in ['planning-memo.md', 'risk-control-matrix.md', 'audit-program.md']:
        (out / name).write_text(f'Computed value {figure}. Reporting year 2026.\n')
    result = invoke(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'figures_checked=3 ' in result.stdout
    (out / 'analytics.json').write_text(json.dumps({'total': value + 1}))
    result = invoke(script)
    assert result.returncode == 1
    assert f'figure {figure} not found' in result.stdout


def test_number_check_accepts_counts_computed_from_sample_csv(tmp_path):
    script,out=qa_fixture(tmp_path,'check_numbers.py')
    (out/'samples').mkdir()
    (out/'samples/T-01.1.csv').write_text('row_id,amount\n'+''.join(f'payment-{i},12.34\n' for i in range(100)))
    for name in ['planning-memo.md','risk-control-matrix.md','audit-program.md']:
        (out/name).write_text('Selected 100 transactions.\n')
    result=invoke(script)
    assert result.returncode==0,result.stdout+result.stderr
    (out/'audit-program.md').write_text('Selected 777 transactions.\n')
    result=invoke(script)
    assert result.returncode==1 and 'figure 777 not found' in result.stdout


@pytest.mark.parametrize('error', [None, 'missing_row', 'wrong_workbook_amount'])
def test_samples_are_checked_against_clean_data_and_original_workbook(tmp_path, error):
    script, out = qa_fixture(tmp_path, 'check_samples.py')
    (out / 'analytics-full').mkdir()
    (out / 'samples').mkdir()
    spend = tmp_path / 'data/spend'
    spend.mkdir(parents=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Data to publish'
    ws.append(['Supplier name', 'Net amount'])
    ws.append(['Fixture supplier', 701 if error == 'wrong_workbook_amount' else 700])
    wb.save(spend / 'example.xlsx')
    (out / 'analytics-full/spend-clean.csv').write_text(
        'row_id,Supplier name,Net amount\nexample.xlsx:2,Fixture supplier,700\n')
    row = 'example.xlsx:999' if error == 'missing_row' else 'example.xlsx:2'
    (out / 'samples/T-01.1.csv').write_text(
        f'row_id,supplier,amount\n{row},Fixture supplier,700\n')
    (out / 'audit-program.md').write_text(f'Payment `{row}`.\n')
    result = invoke(script)
    assert result.returncode == (1 if error else 0), result.stdout + result.stderr
    if error == 'missing_row':
        assert 'not in spend-clean.csv' in result.stdout
    elif error == 'wrong_workbook_amount':
        assert 'different supplier or amount' in result.stdout
