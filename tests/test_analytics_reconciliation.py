"""Independently reconcile the actual spend outputs to the immutable workbooks."""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ['Service', 'Expenditure category', 'Narrative', 'Date', 'Net amount', 'Supplier name']


def original_rows():
    result = {}
    for path in sorted((ROOT / 'data/spend').glob('*.xlsx')):
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet = workbook['Data to publish']
        header = None
        for number, values in enumerate(sheet.iter_rows(values_only=True), 1):
            if header is None:
                if list(values[:6]) == HEADERS:
                    header = list(values[:6])
                continue
            if all(value is None for value in values):
                continue
            row = dict(zip(header, values))
            if row['Net amount'] is None:
                continue
            result[f'{path.name}:{number}'] = row
        workbook.close()
    return result


def read_rows(name):
    with (ROOT / 'outputs/analytics-full' / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def test_source_inputs_remain_byte_for_byte_unchanged():
    manifest = json.loads((ROOT / 'evidence/source-manifest.json').read_text())
    for item in manifest['files']:
        assert hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest() == item['sha256']


def test_each_original_payment_is_kept_or_logged_once_with_exact_row_and_amount():
    source = original_rows()
    kept = read_rows('spend-clean.csv')
    excluded = read_rows('spend-excluded.csv')
    all_rows = kept + excluded
    ids = [r['row_id'] for r in all_rows]
    assert len(ids) == len(set(ids)), 'Payments must not be duplicated across outputs.'
    assert set(ids) == set(source), 'Every original payment must be accounted for.'
    for row in all_rows:
        original = source[row['row_id']]
        assert row['Supplier name'].strip() == str(original['Supplier name']).strip()
        assert Decimal(row['Net amount']).quantize(Decimal('.01')) == Decimal(str(original['Net amount'])).quantize(Decimal('.01'))


def test_population_counts_and_totals_reconcile_to_cleaned_population():
    source = original_rows()
    kept = read_rows('spend-clean.csv')
    analytics = json.loads((ROOT / 'outputs/analytics.json').read_text())
    population = analytics['population']
    assert population['rows_raw'] == len(source)
    assert population['rows_after_exclusions'] == len(kept)
    expected = sum((Decimal(row['Net amount']) for row in kept), Decimal(0)).quantize(Decimal('.01'))
    assert Decimal(str(population['total_gbp'])).quantize(Decimal('.01')) == expected
    assert set(analytics['tests']) == {'threshold_clustering', 'split_purchases', 'high_value_suppliers',
                                     'off_contract', 'duplicates', 'expired_notice_spend', 'spend_vs_award'}
