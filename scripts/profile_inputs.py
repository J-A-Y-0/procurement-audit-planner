"""Reproduce the input inventory without printing transaction tables."""
import json
from pathlib import Path

from spend_inputs import read_workbooks


def main():
    root = Path(__file__).resolve().parents[1]
    frame = read_workbooks(list((root / 'data/spend').glob('*.xlsx')))
    report = {'rows_raw': len(frame), 'files': frame.groupby('source_file').size().to_dict(),
              'date_min': frame.pay_date.min(), 'date_max': frame.pay_date.max(),
              'raw_gbp': round(float(frame['Net amount'].sum()), 2)}
    (root / 'evidence/input-profile.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
