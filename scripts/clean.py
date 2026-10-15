"""Clean spend workbooks and the contracts.csv notice export.

Writes:
  outputs/analytics-full/spend-clean.csv
  outputs/analytics-full/spend-excluded.csv
  outputs/analytics-full/notices-clean.csv
  outputs/analytics-full/cleaning-log.json

No thresholds are embedded here; this script only cleans, tags and logs.
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import normalise_supplier  # noqa: E402
from spend_inputs import read_workbooks  # noqa: E402

OUT = ROOT / 'outputs' / 'analytics-full'
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED_COLUMNS = ['Service', 'Expenditure category', 'Narrative', 'Date', 'Net amount', 'Supplier name']

# --- Exclusion regexes (logged verbatim below) ---
RE_PENSION = re.compile(r'LGPS|PENSION|SUPERANNUATION', re.IGNORECASE)
RE_INTER_AUTHORITY_SUPPLIER = re.compile(
    r'\b(COUNCIL|BOROUGH|COUNTY|CNCL|NHS|POLICE|FIRE AUTHORITY|FIRE AND RESCUE|HMRC|HM REVENUE|'
    r'DEPARTMENT FOR|MINISTRY OF)\b', re.IGNORECASE)
RE_JOINT_ARRANGEMENTS = re.compile(r'JOINT ARRANGEMENTS', re.IGNORECASE)

# --- Tagging regexes (logged verbatim below; first match wins) ---
PLACEMENT_SERVICE_PREFIXES = ("Adult Social Care", "Children's Social Care", "Education")
PLACEMENT_NARRATIVES = {"Private Contractors", "Other agencies", "Voluntary Associations"}
RE_GRANT = re.compile(r'GRANT', re.IGNORECASE)
RE_AGENCY = re.compile(r'AGENCY', re.IGNORECASE)
RE_PREMISES = re.compile(r'RENT|RATES|WATER RATES|LEASE', re.IGNORECASE)

TAGGING_REGEXES = {
    'care_or_education_placement': (
        "Service startswith one of %r AND Narrative in %r" % (PLACEMENT_SERVICE_PREFIXES, sorted(PLACEMENT_NARRATIVES))
    ),
    'grant': RE_GRANT.pattern,
    'agency_staff': RE_AGENCY.pattern,
    'premises_non_procurement': RE_PREMISES.pattern,
    'general_procurement': 'everything else (first-match-wins fallthrough)',
}


def tag_row(service, narrative):
    service = '' if service is None else str(service)
    narrative = '' if narrative is None else str(narrative)
    if service.startswith(PLACEMENT_SERVICE_PREFIXES) and narrative in PLACEMENT_NARRATIVES:
        return 'care_or_education_placement'
    if RE_GRANT.search(narrative):
        return 'grant'
    if RE_AGENCY.search(narrative):
        return 'agency_staff'
    if RE_PREMISES.search(narrative):
        return 'premises_non_procurement'
    return 'general_procurement'


def load_spend():
    paths = sorted((ROOT / 'data' / 'spend').glob('*.xlsx'))
    if not paths:
        print('STOP: no spend workbooks found under data/spend', file=sys.stderr)
        sys.exit(1)
    try:
        df = read_workbooks(paths)
    except ValueError as error:
        print(f'STOP: {error}', file=sys.stderr)
        sys.exit(1)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        print(f'STOP: spend data missing expected columns: {missing}', file=sys.stderr)
        sys.exit(1)

    if df[['pay_date', 'Net amount', 'Supplier name']].isna().any().any():
        print('STOP: null date, amount or supplier present in spend data', file=sys.stderr)
        sys.exit(1)
    if (df['Net amount'] < 0).any():
        print('STOP: negative Net amount present in spend data', file=sys.stderr)
        sys.exit(1)

    df['pay_date'] = pd.to_datetime(df['pay_date']).dt.date
    return df


def classify_exclusion(row):
    supplier_upper = str(row['Supplier name']).strip().upper()
    narrative = '' if row['Narrative'] is None else str(row['Narrative'])
    if supplier_upper == 'REDACTED':
        return 'redacted_supplier'
    if RE_PENSION.search(narrative):
        return 'pension_statutory'
    if narrative.strip() != 'Private Contractors' and (
        RE_INTER_AUTHORITY_SUPPLIER.search(str(row['Supplier name'])) or RE_JOINT_ARRANGEMENTS.search(narrative)
    ):
        return 'inter_authority'
    return None


def clean_spend(df):
    df = df.copy()
    df['exclusion_reason'] = df.apply(classify_exclusion, axis=1)
    excluded_mask = df['exclusion_reason'].notna()
    excluded = df[excluded_mask].copy()
    kept = df[~excluded_mask].copy()
    kept['tag'] = kept.apply(lambda r: tag_row(r['Service'], r['Narrative']), axis=1)

    exclusion_log = {}
    for reason, group in excluded.groupby('exclusion_reason'):
        exclusion_log[reason] = {
            'rows': int(len(group)),
            'gbp': float(group['Net amount'].sum()),
            'reason': {
                'redacted_supplier': 'Supplier name is Redacted (case-insensitive): many individuals under one label, never used supplier-level.',
                'pension_statutory': 'Narrative matches LGPS|PENSION|SUPERANNUATION: statutory pension contributions, not procurement spend.',
                'inter_authority': 'Supplier or narrative indicates an inter-authority/statutory body payment (and narrative is not Private Contractors): not open-market procurement.',
            }[reason],
        }
    for reason in ('redacted_supplier', 'pension_statutory', 'inter_authority'):
        exclusion_log.setdefault(reason, {'rows': 0, 'gbp': 0.0, 'reason': 'no rows matched'})

    months_covered = kept['pay_date'].apply(lambda d: (d.year, d.month)).nunique()

    return kept, excluded, exclusion_log, months_covered


def write_spend_outputs(kept, excluded):
    kept_out = kept.drop(columns=['exclusion_reason'])
    kept_out.to_csv(OUT / 'spend-clean.csv', index=False)
    excluded.to_csv(OUT / 'spend-excluded.csv', index=False)


# --- Contracts loading ---

def notice_date(value, column):
    if pd.isna(value) or not str(value).strip():
        return None
    try:
        return datetime.strptime(str(value).strip(), '%d/%m/%Y').date()
    except ValueError as error:
        raise ValueError(f'malformed notice date in {column}: {value!r}') from error


def published_date(value):
    if pd.isna(value) or not re.match(r'^\d{4}-\d{2}-\d{2}(?:T|$)', str(value).strip()):
        raise ValueError(f'malformed ISO publication date: {value!r}')
    try:
        return datetime.fromisoformat(str(value).strip().replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError(f'malformed ISO publication date: {value!r}') from error

def load_contracts(spend_window_start):
    path = ROOT / 'data' / 'contracts.csv'
    contracts_present = path.exists()
    log = {'contracts_present': contracts_present, 'register_present': False}
    if not contracts_present:
        log.update({
            'rows_in_file': 0, 'rows_for_council': 0, 'notice_supplier_pairs': 0,
            'distinct_suppliers': 0, 'active_in_window': 0, 'ended_before_window': 0,
            'zero_value_awards': 0, 'rows_per_year': {}, 'published_range': [None, None],
            'warnings': ['data/contracts.csv not present: notice-based tests skipped'],
            'organisation_names_kept': [], 'organisation_names_dropped_counts': {},
        })
        pd.DataFrame(columns=['notice_id', 'supplier_raw', 'supplier_norm', 'companies_house_number',
                               'title', 'ojeu_procedure_type', 'awarded_value', 'suppliers_on_notice',
                               'contract_start', 'contract_end', 'awarded_date', 'published_date',
                               'active', 'ended']).to_csv(OUT / 'notices-clean.csv', index=False)
        return pd.DataFrame(), log

    raw = pd.read_csv(path)
    rows_in_file = len(raw)

    org_counts_all = raw['Organisation Name'].value_counts().to_dict()
    org_norm = raw['Organisation Name'].astype(str).str.strip().str.upper()
    keep_mask = org_norm.isin({'WEST BERKSHIRE COUNCIL', 'WEST BERKSHIRE'})
    kept_orgs = raw[keep_mask]
    dropped_orgs = raw[~keep_mask]
    org_names_kept = sorted(kept_orgs['Organisation Name'].unique().tolist())
    org_names_dropped_counts = dropped_orgs['Organisation Name'].value_counts().to_dict()

    rows_for_council = len(kept_orgs)
    if rows_for_council < 20:
        # Treat as absent per non-negotiable rule 4.
        log.update({
            'rows_in_file': rows_in_file, 'rows_for_council': rows_for_council,
            'notice_supplier_pairs': 0, 'distinct_suppliers': 0, 'active_in_window': 0,
            'ended_before_window': 0, 'zero_value_awards': 0, 'rows_per_year': {},
            'published_range': [None, None],
            'warnings': [f'only {rows_for_council} notices remain for the council after filtering '
                         '(<20): treated as absent'],
            'organisation_names_kept': org_names_kept,
            'organisation_names_dropped_counts': org_names_dropped_counts,
        })
        log['contracts_present'] = False
        pd.DataFrame(columns=['notice_id', 'supplier_raw', 'supplier_norm', 'companies_house_number',
                               'title', 'ojeu_procedure_type', 'awarded_value', 'suppliers_on_notice',
                               'contract_start', 'contract_end', 'awarded_date', 'published_date',
                               'active', 'ended']).to_csv(OUT / 'notices-clean.csv', index=False)
        return pd.DataFrame(), log

    col = 'Supplier [Name|Address|Ref type|Ref Number|Is SME|Is VCSE]'
    records = []
    for _, row in kept_orgs.iterrows():
        packed = row[col]
        if pd.isna(packed):
            continue
        blocks = str(packed).strip()
        if blocks.startswith('['):
            blocks = blocks[1:]
        if blocks.endswith(']'):
            blocks = blocks[:-1]
        parts = blocks.split('][')
        suppliers_on_notice = len(parts)
        contract_start = notice_date(row['Contract start date'], 'Contract start date')
        contract_end = notice_date(row['Contract end date'], 'Contract end date')
        awarded_date = notice_date(row['Awarded Date'], 'Awarded Date')
        publication = published_date(row['Published Date'])
        if contract_start and contract_end and contract_end <= contract_start:
            raise ValueError(f'notice term ends on/before start: {row["Notice Identifier"]}')

        active = contract_end is None or contract_end >= spend_window_start
        for block in parts:
            fields = block.split('|')
            name = fields[0] if len(fields) > 0 else None
            ref_type = fields[2] if len(fields) > 2 else None
            ch_number = fields[3] if len(fields) > 3 and ref_type == 'COMPANIES_HOUSE' else None
            if not name:
                continue
            records.append({
                'notice_id': row['Notice Identifier'],
                'source': 'contracts_finder',
                'title': row['Title'],
                'supplier_raw': name,
                'supplier_norm': normalise_supplier(name),
                'companies_house_number': ch_number,
                'ojeu_procedure_type': row.get('OJEU Procedure Type'),
                'awarded_value': row['Awarded Value'],
                'suppliers_on_notice': suppliers_on_notice,
                'contract_start': contract_start.isoformat() if contract_start else None,
                'contract_end': contract_end.isoformat() if contract_end else None,
                'awarded_date': awarded_date.isoformat() if awarded_date else None,
                'published_date': publication.isoformat(),
                'published_year': publication.year,
                'active': bool(active),
                'ended': not bool(active),
            })

    notices = pd.DataFrame(records)
    notices.to_csv(OUT / 'notices-clean.csv', index=False)

    unique_notices = notices.drop_duplicates('notice_id')
    rows_per_year = unique_notices['published_year'].dropna().astype(int).value_counts().sort_index().to_dict()
    rows_per_year = {str(k): int(v) for k, v in rows_per_year.items()}

    warnings = []
    if rows_in_file == 1000:
        warnings.append('source file has exactly 1000 rows: possible Contracts Finder export cap')
    thin_years = [y for y, c in rows_per_year.items() if c <= 1]
    if thin_years:
        warnings.append(f'publication years with <=1 notice look implausibly thin: {thin_years}')

    zero_value_awards = int((kept_orgs['Awarded Value'].fillna(0) == 0).sum())

    log.update({
        'rows_in_file': rows_in_file,
        'rows_for_council': rows_for_council,
        'notice_supplier_pairs': int(len(notices)),
        'distinct_suppliers': int(notices['supplier_norm'].nunique()) if len(notices) else 0,
        'active_in_window': int(unique_notices['active'].sum()) if len(notices) else 0,
        'ended_before_window': int(unique_notices['ended'].sum()) if len(notices) else 0,
        'active_notice_supplier_pairs': int(notices['active'].sum()),
        'ended_notice_supplier_pairs': int(notices['ended'].sum()),
        'count_units': 'rows_for_council/rows_per_year/active_in_window/ended_before_window count notices; pair fields count exploded notice-supplier pairs',
        'zero_value_awards': zero_value_awards,
        'rows_per_year': rows_per_year,
        'published_range': [
            notices['published_date'].dropna().min() if len(notices) else None,
            notices['published_date'].dropna().max() if len(notices) else None,
        ],
        'warnings': warnings,
        'organisation_names_kept': org_names_kept,
        'organisation_names_dropped_counts': {str(k): int(v) for k, v in org_names_dropped_counts.items()},
        'organisation_names_all_counts': {str(k): int(v) for k, v in org_counts_all.items()},
    })
    return notices, log


def load_register(spend_window_start=None):
    path = ROOT / 'data' / 'contract-register.csv'
    if not path.exists():
        return None, {'register_present': False}
    raw = pd.read_csv(path)
    aliases = {re.sub(r'[^a-z0-9]','',c.lower()):c for c in raw.columns}
    def column(*choices):
        return next((aliases[c] for c in choices if c in aliases),None)
    supplier = column('supplier','suppliername','contractor','contractorname')
    start_col = column('startdate','contractstartdate','start')
    end_col = column('enddate','contractenddate','end','expirydate')
    value_col = column('value','contractvalue','awardedvalue')
    if not supplier or not end_col:
        raise ValueError('optional register needs mapped supplier and end-date columns; inspect header before mapping')
    def iso(value):
        if pd.isna(value) or not str(value).strip():return None
        try:return datetime.strptime(str(value).strip(),'%Y-%m-%d').date()
        except ValueError as error:raise ValueError('optional register dates must be explicit YYYY-MM-DD; inspect other formats before mapping') from error
    records=[]
    for i,row in raw.iterrows():
        if pd.isna(row[supplier]) or not str(row[supplier]).strip():raise ValueError('optional register has missing supplier')
        start=iso(row[start_col]) if start_col else None
        end=iso(row[end_col])
        if start and end and end<=start:raise ValueError('optional register term ends on/before start')
        active=end is None or spend_window_start is None or end>=spend_window_start
        records.append({'notice_id':f'register:{i+2}','source':'register','supplier_raw':row[supplier],
            'supplier_norm':normalise_supplier(row[supplier]),'contract_start':start.isoformat() if start else None,
            'contract_end':end.isoformat() if end else None,'active':active,'ended':not active,
            'awarded_value':row[value_col] if value_col else None,'suppliers_on_notice':1})
    result=pd.DataFrame(records,columns=['notice_id','source','supplier_raw','supplier_norm','contract_start','contract_end','active','ended','awarded_value','suppliers_on_notice'])
    result.to_csv(OUT/'register-clean.csv',index=False)
    return result,{'register_present':True,'rows':len(result),'active_rows':int(result.active.sum()),
                   'column_mapping':{'supplier':supplier,'start':start_col,'end':end_col,'value':value_col},'date_format':'%Y-%m-%d'}


def main():
    df = load_spend()
    kept, excluded, exclusion_log, months_covered = clean_spend(df)
    write_spend_outputs(kept, excluded)

    spend_window_start = min(kept['pay_date'])
    notices, contracts_log = load_contracts(spend_window_start)
    register_frame, register_log = load_register(spend_window_start)
    contracts_log['register_present']=register_log['register_present']

    tag_counts = {}
    for tag, group in kept.groupby('tag'):
        tag_counts[tag] = {
            'rows': int(len(group)),
            'gbp': float(group['Net amount'].sum()),
            'suppliers': int(group.loc[group['Supplier name'].str.upper() != 'REDACTED', 'supplier_norm'].nunique()),
        }
    for tag in ('care_or_education_placement', 'grant', 'agency_staff', 'premises_non_procurement', 'general_procurement'):
        tag_counts.setdefault(tag, {'rows': 0, 'gbp': 0.0, 'suppliers': 0})

    cleaning_log = {
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'spend_files': [p.name for p in sorted((ROOT / 'data' / 'spend').glob('*.xlsx'))],
        'rows_raw': int(len(df)),
        'rows_after_exclusions': int(len(kept)),
        'date_min': df['pay_date'].min().isoformat(),
        'date_max': df['pay_date'].max().isoformat(),
        'months_covered': int(months_covered),
        'spend_window_start': spend_window_start.isoformat(),
        'total_gbp_after_exclusions': float(kept['Net amount'].sum()),
        'exclusions': exclusion_log,
        'exclusion_regexes': {
            'redacted_supplier': 'Supplier name equals REDACTED (case-insensitive)',
            'pension_statutory': RE_PENSION.pattern,
            'inter_authority': RE_INTER_AUTHORITY_SUPPLIER.pattern + ' OR narrative matches ' + RE_JOINT_ARRANGEMENTS.pattern
                                + ' ; applied only when narrative != "Private Contractors"',
        },
        'tags': tag_counts,
        'tagging_regexes': TAGGING_REGEXES,
        'contracts': contracts_log,
        'register': register_log,
    }
    with (OUT / 'cleaning-log.json').open('w') as fh:
        json.dump(cleaning_log, fh, indent=2, default=str)

    print('clean.py complete')
    print(f"rows_raw={cleaning_log['rows_raw']} rows_after_exclusions={cleaning_log['rows_after_exclusions']}")
    print(f"months_covered={cleaning_log['months_covered']}")
    print(f"contracts_present={contracts_log['contracts_present']} register_present={register_log['register_present']}")


if __name__ == '__main__':
    main()
