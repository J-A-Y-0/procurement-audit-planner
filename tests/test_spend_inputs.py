"""Hand-checked fixtures for the variable headers, dates and supplier keys."""
import sys
from pathlib import Path
from datetime import datetime

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import normalise_supplier, parse_spend_date
from spend_inputs import read_workbooks


@pytest.mark.parametrize(('raw', 'expected'), [
    ('The Acme (CHAPS ONLY) Limited T/A Trading Brand', 'ACME'),
    ('A & B Services UK LLP', 'A AND B SERVICES'),
    ('Example PLC', 'EXAMPLE'),
    ('Example Ltd trading as Sample', 'EXAMPLE'),
])
def test_supplier_normalisation(raw, expected):
    assert normalise_supplier(raw) == expected


def test_text_dates_are_month_first_without_automatic_detection():
    assert parse_spend_date('5/6/26').date().isoformat() == '2026-05-06'
    with pytest.raises(ValueError):
        parse_spend_date('31/05/2026')


def workbook(path, blank_header_row=False, missing_column=False):
    w = openpyxl.Workbook()
    s = w.active
    s.title = 'Data to publish'
    if blank_header_row:
        s.append([None] * 6)
    names = ['Service', 'Expenditure category', 'Narrative', 'Date', 'Net amount', 'Supplier name']
    s.append(names[:-1] if missing_column else names)
    s.append(['Service', 'Supplies', 'Example', datetime(2026, 5, 6, 12), 700.25, 'Example Ltd'])
    w.save(path)


@pytest.mark.parametrize('blank_header_row', [False, True])
def test_headers_are_detected_and_original_sheet_rows_preserved(tmp_path, blank_header_row):
    source = tmp_path / 'example.xlsx'
    workbook(source, blank_header_row)
    frame = read_workbooks([source])
    assert len(frame) == 1
    assert frame.iloc[0]['row_id'] == f'example.xlsx:{3 if blank_header_row else 2}'
    assert frame.iloc[0]['Net amount'] == 700.25
    assert frame.iloc[0]['supplier_norm'] == 'EXAMPLE'
    assert frame.iloc[0]['pay_date'] == '2026-05-06'


def test_missing_required_column_stops_processing(tmp_path):
    source = tmp_path / 'bad.xlsx'
    workbook(source, missing_column=True)
    with pytest.raises(ValueError, match='header'):
        read_workbooks([source])
