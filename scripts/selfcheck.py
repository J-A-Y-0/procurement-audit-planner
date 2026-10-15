"""Re-derive one flagged item per test, plus matching/duplicate reconciliation.

Payment totals are independently summed from spend-clean.csv; notice assertions
are rebuilt from the original raw Contracts Finder CSV rather than rate outputs.
Only the chosen checks and a few original workbook row IDs are printed.
"""
import ast
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from common import normalise_supplier

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / 'outputs/analytics-full'
spend = pd.read_csv(FULL / 'spend-clean.csv')
spend['calendar'] = pd.to_datetime(spend['pay_date'])
a = json.loads((ROOT / 'outputs/analytics.json').read_text())
tests = a['tests']
factor = Decimal(12) / Decimal(a['population']['months_covered'])


def money(values):
    return sum((Decimal(str(x)).quantize(Decimal('.01')) for x in values), Decimal(0))


def equal(left, right):
    assert Decimal(str(left)).quantize(Decimal('.01')) == Decimal(str(right)).quantize(Decimal('.01')), (left, right)


def report(name, detail, rows=None):
    print(f'PASS {name}: {detail}')
    if rows is not None:
        print('  source row_ids:', rows['row_id'].head(3).tolist())


# The threshold is selected from the run, not hardcoded into the check.
tc = max(tests['threshold_clustering'].values(), key=lambda x:x['band_90pct_to_threshold']['count'])
t = Decimal(str(tc['threshold_value']))
amounts = spend['Net amount'].map(lambda x:Decimal(str(x)))
band = spend[(amounts >= t*Decimal('.9')) & ((amounts < t) if tc['inclusive'] else (amounts <= t))]
assert len(band) == tc['band_90pct_to_threshold']['count']
equal(money(band['Net amount']), tc['band_90pct_to_threshold']['gbp'])
report('threshold_clustering', f"threshold={t}; rows={len(band)}; GBP={money(band['Net amount'])}", band)

windows = [(key, item) for key, value in tests['split_purchases'].items() for item in value['top20_windows']]
if windows:
    key, item = max(windows, key=lambda pair:pair[1]['total_gbp'])
    rows = spend[(spend.supplier_norm == item['supplier_norm']) & (spend['Net amount'] < float(key)) &
                 (spend.calendar >= pd.Timestamp(item['window_start'])) & (spend.calendar <= pd.Timestamp(item['window_end']))]
    assert set(rows.row_id) == set(item['row_ids']) and len(rows) == item['n_payments']
    equal(money(rows['Net amount']), item['total_gbp'])
    report('split_purchases', f"threshold={key}; rows={len(rows)}; GBP={money(rows['Net amount'])}", rows)
else:
    report('split_purchases', 'no flagged window; zero population recorded')

item = tests['high_value_suppliers']['headline_general_procurement']['top20'][0]
rows = spend[spend.supplier_norm == item['supplier_norm']]
equal(money(rows['Net amount']), item['total_gbp'])
equal(money(rows['Net amount'])*factor, item['annualised_estimate'])
report('high_value_suppliers', f"period GBP={money(rows['Net amount'])}; annualised estimate GBP={money(rows['Net amount'])*factor}", rows)

# Independently explode the raw export and parse explicit day/month/year dates.
raw_notices = []
if a['contracts']['contracts_present']:
    raw = pd.read_csv(ROOT / 'data/contracts.csv', keep_default_na=False)
    start = datetime.strptime(a['population']['date_min'], '%Y-%m-%d').date()
    for row in raw.to_dict('records'):
        if row['Organisation Name'].strip().upper() not in ('WEST BERKSHIRE COUNCIL', 'WEST BERKSHIRE'):
            continue
        blocks = row['Supplier [Name|Address|Ref type|Ref Number|Is SME|Is VCSE]'].strip('[]').split('][')
        for block in blocks:
            end = datetime.strptime(row['Contract end date'], '%d/%m/%Y').date() if row['Contract end date'] else None
            raw_notices.append({'supplier': normalise_supplier(block.split('|')[0]),
                'end': end, 'active': end is None or end >= start, 'notice': row, 'n_suppliers': len(blocks)})

oc = tests['off_contract']
if not oc.get('skipped'):
    suppliers = pd.read_csv(FULL / 'high_value_suppliers_all.csv')
    boundary = oc['parameters']['publication_threshold']
    eligible = suppliers[suppliers.annualised_estimate >= boundary if oc['parameters']['inclusive'] else suppliers.annualised_estimate > boundary]
    active_names = {n['supplier'] for n in raw_notices if n['active']}
    exact = int(eligible.supplier_norm.isin(active_names).sum())
    declared_exact = sum(v['count'] for v in oc['counts_by_match_class'] if v['match_class'] == 'exact')
    assert exact == declared_exact
    assert sum(v['count'] for v in oc['counts_by_match_class']) == len(eligible)
    selected = eligible[~eligible.supplier_norm.isin(active_names)].iloc[0]
    rows = spend[spend.supplier_norm == selected.supplier_norm]
    equal(money(rows['Net amount'])*factor, selected.annualised_estimate)
    report('off_contract', f'eligible suppliers={len(eligible)}; exact active names={exact}; near names remain unconfirmed', rows)
else:
    report('off_contract', 'skipped with recorded reason: '+oc['reason'])

# Reconcile all overlap-attributed extras before checking one bounded group.
groups = pd.read_csv(FULL / 'duplicates.csv')
seen = set()
for group in groups.to_dict('records'):
    ids = ast.literal_eval(group['row_ids'])
    extras = ast.literal_eval(group['attributed_extra_row_ids'])
    assert set(extras).issubset(ids) and not seen.intersection(extras)
    seen.update(extras)
    rows = spend[spend.row_id.isin(ids)]
    assert len(rows) == len(ids) == group['n_rows']
    assert rows.supplier_norm.nunique() == 1 and rows['Net amount'].nunique() == 1
    assert (rows.calendar.max()-rows.calendar.min()).days <= 7
    assert (rows.Date.nunique() == 1) == (group['tier'] == 'same_timestamp')
    equal(money([group['amount']] * len(extras)), group['gbp_beyond_first'])
for tier in ('same_timestamp','different_time'):
    equal(money(groups.loc[groups.tier == tier,'gbp_beyond_first']), tests['duplicates'][tier]['gbp_beyond_first_instance'])
if len(groups):
    item = groups.sort_values('gbp_beyond_first',ascending=False).iloc[0]
    rows = spend[spend.row_id.isin(ast.literal_eval(item.row_ids))]
    report('duplicates', f"bounded groups={len(groups)}; independently verified unique attributed extra rows={len(seen)}", rows)
else:
    report('duplicates', 'no flagged equal-amount group')

exp = tests['expired_notice_spend']
if exp.get('top20'):
    item = exp['top20'][0]; rows = spend[spend.supplier_norm == item['supplier_norm']]
    matched = [n for n in raw_notices if n['supplier'] == item['supplier_norm']]
    assert matched and all(n['end'] is not None and n['end'] < start for n in matched)
    assert max(n['end'] for n in matched).isoformat() == item['latest_notice_end_date']
    equal(money(rows['Net amount'])*factor, item['annualised_estimate'])
    report('expired_notice_spend', f"latest end={item['latest_notice_end_date']}; annualised estimate GBP={money(rows['Net amount'])*factor}", rows)
else:
    report('expired_notice_spend', exp.get('reason','no flagged supplier'))

sva = tests['spend_vs_award']
if sva.get('top20'):
    item = sva['top20'][0]; rows = spend[spend.supplier_norm == item['supplier_norm']]
    matched = [n for n in raw_notices if n['supplier'] == item['supplier_norm'] and n['active']]
    assert len({n['notice']['Notice Identifier'] for n in matched}) == 1
    notice = next(n for n in matched if n['notice']['Notice Identifier'] == item['notice_id'])
    assert notice['n_suppliers'] == 1
    raw = notice['notice']
    years = (datetime.strptime(raw['Contract end date'],'%d/%m/%Y')-datetime.strptime(raw['Contract start date'],'%d/%m/%Y')).days/365.25
    annual_rate = float(raw['Awarded Value'])/years
    independent_ratio = float(money(rows['Net amount'])*factor)/annual_rate
    assert abs(independent_ratio-item['ratio']) < 1e-9
    report('spend_vs_award', f"independently rebuilt award annual rate={annual_rate:.6f}; ratio={independent_ratio:.6f}", rows)
else:
    report('spend_vs_award', sva.get('reason','no flagged supplier'))
print('All seven self-checks passed.')
