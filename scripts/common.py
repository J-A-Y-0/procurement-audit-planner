"""Shared, deterministic data parsing; no thresholds are embedded here."""
import re
from datetime import datetime


def normalise_supplier(value):
    text = str(value).upper().replace('&', ' AND ')
    text = re.sub(r'\([^)]*\)', ' ', text)
    text = re.split(r'\bT\s*/\s*A\b|\bTRADING\s+AS\b', text, maxsplit=1)[0]
    text = re.sub(r'[^A-Z0-9 ]', ' ', text)
    dropped = {'LTD', 'LIMITED', 'PLC', 'LLP', 'LLC', 'INC', 'CIC', 'CIO', 'UK', 'THE'}
    return ' '.join(token for token in text.split() if token not in dropped)


def parse_spend_date(value):
    if isinstance(value, datetime):
        return value
    for fmt in ('%m/%d/%y', '%m/%d/%Y', '%m/%d/%y %H:%M:%S', '%m/%d/%Y %H:%M:%S'):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            pass
    raise ValueError(f'Invalid month-first spend date: {value!r}')
