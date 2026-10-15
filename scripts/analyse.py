"""Analyse the cleaned spend population against rules.json thresholds.

Reads outputs/analytics-full/spend-clean.csv (+ notices-clean.csv + cleaning-log.json),
writes per-test CSVs to outputs/analytics-full/ and outputs/analytics.json.
No thresholds are typed in here: every numeric boundary is read from rules.json.
"""
import difflib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / 'outputs' / 'analytics-full'

CAVEAT_TEXT = (
    "contracts.csv holds published notices, not a contract register. It holds awards published on "
    "Contracts Finder in roughly the last five years. A contract awarded earlier (e.g. long-running "
    "waste or highways contracts), one advertised only on Find a Tender, a framework call-off recorded "
    "under another buyer, or an exempt placement will have no notice here. \"No notice found\" is "
    "therefore an indicator to check against the council's contract register, never evidence of "
    "off-contract spend."
)

GENERIC_WORDS = set("""AND OF THE SERVICES SERVICE GROUP CARE COMPANY HOMES
HOME HOUSE UNIVERSITY COUNCIL TRUST SOLUTIONS CONSULTANCY CONSULTING
ASSOCIATES PARTNERSHIP NETWORK CENTRE CENTER TRAVEL CARS COACHES TAXIS
CONSTRUCTION HEALTHCARE HEALTH SCHOOL SCHOOLS EDUCATION SUPPORT LIVING
CHILDREN CHILDRENS SEN BERKSHIRE WEST SOUTH NORTH EAST READING NEWBURY
THATCHAM HUNGERFORD SOUTHERN SYSTEMS SOFTWARE HOUSING SECURITY CLEANING
FOSTERING COMMUNITY BUSINESS MANAGEMENT FACILITIES SUPPLIES CATERING
TRANSPORT ENGINEERING HIRE PROPERTY PROPERTIES VALLEY""".split())


def distinctive_tokens(name):
    return {t for t in name.split() if t not in GENERIC_WORDS and len(t) >= 3}


# ---------- Step 1: rules / thresholds ----------

def load_rules():
    with (ROOT / 'outputs' / 'rules.json').open() as fh:
        return json.load(fh)


def build_thresholds(rules_doc):
    """Every distinct numeric threshold_low/threshold_high from threshold/approver/anti-avoidance rules."""
    values = {}  # value -> {rule_ids:set, inclusive_votes:list(bool), competition_rule_ids:set}

    def add(value, inclusive, rule_id, competition, bound):
        if value is None:
            return
        entry = values.setdefault(value, {'rule_ids': set(), 'inclusive_votes': [], 'competition_rule_ids': set(), 'rule_boundaries':[]})
        entry['rule_ids'].add(rule_id)
        entry['inclusive_votes'].append(bool(inclusive))
        entry['rule_boundaries'].append({'rule_id':rule_id,'bound':bound,'inclusive':inclusive,
                                        'scope':rule.get('scope','all')})
        if competition:
            entry['competition_rule_ids'].add(rule_id)

    skipped_null_params = []
    for rule in rules_doc['rules']:
        if rule.get('type') not in ('threshold', 'approver', 'anti-avoidance'):
            continue
        action = (rule.get('required_action') or '').lower()
        # Narrow definition: action text must indicate OBTAINING quotes/tenders (not merely publishing/approving).
        is_competition = (
            ('obtain' in action and ('quote' in action or 'tender' in action))
            or ('send invitations to quote' in action)
            or ('seek' in action and ('quote' in action or 'tender' in action))
        )
        low = rule.get('threshold_low')
        high = rule.get('threshold_high')
        if low is not None:
            add(low, rule.get('threshold_low_inclusive'), rule['rule_id'], is_competition, 'lower')
        if high is not None:
            add(high, rule.get('threshold_high_inclusive'), rule['rule_id'], is_competition, 'upper')
        for ref_field, ref_name in (('threshold_low_ref', rule.get('threshold_low_ref')),
                                     ('threshold_high_ref', rule.get('threshold_high_ref'))):
            if ref_name and rules_doc['parameters'].get(ref_name, {}).get('value') is None:
                skipped_null_params.append({
                    'rule_id': rule['rule_id'], 'parameter': ref_name,
                    'reason': f'{ref_name} is null in rules.json parameters',
                })
            elif ref_name:
                bound = ref_field.removesuffix('_ref')
                add(rules_doc['parameters'][ref_name]['value'], rule.get(bound + '_inclusive'),
                    rule['rule_id'], is_competition, bound.removeprefix('threshold_'))

    thresholds = []
    for value, entry in sorted(values.items()):
        inclusive = any(entry['inclusive_votes'])  # if any citing rule treats the value as inclusive, say so
        thresholds.append({
            'value': value,
            'inclusive': inclusive,
            'rule_ids': sorted(entry['rule_ids']),
            'competition_triggering': bool(entry['competition_rule_ids']),
            'competition_triggering_rule_ids': sorted(entry['competition_rule_ids']),
            'rule_boundaries':entry['rule_boundaries'],
            'inclusivity_note':'Exploratory shared boundary uses inclusive if any source band includes it; rule-specific lower/upper boundaries and category scopes remain above. This is not a determination of the applicable contract route.',
        })
    return thresholds, skipped_null_params


# ---------- Supplier matching ----------

def match_supplier(spend_name_norm, active_notice_names_norm, spend_name_counts, notice_name_counts):
    if spend_name_norm in active_notice_names_norm:
        return 'exact', spend_name_norm, 'exact normalised-name match'
    best = (None, 0.0)
    for notice_name in sorted(active_notice_names_norm):
        ratio = difflib.SequenceMatcher(None, spend_name_norm, notice_name).ratio()
        if ratio > best[1]:
            best = (notice_name, ratio)
    if best[1] >= 0.85:
        return 'near_ratio', best[0], f'SequenceMatcher ratio {best[1]:.3f}'

    spend_tokens = distinctive_tokens(spend_name_norm)
    best_contain = None
    for notice_name in sorted(active_notice_names_norm):
        notice_tokens = distinctive_tokens(notice_name)
        smaller, larger = (spend_tokens, notice_tokens) if len(spend_tokens) <= len(notice_tokens) else (notice_tokens, spend_tokens)
        if not smaller or not smaller.issubset(larger):
            continue
        if len(smaller) >= 2:
            best_contain = notice_name
            break
        token = next(iter(smaller))
        if spend_name_counts.get(token, 0) == 1 and notice_name_counts.get(token, 0) == 1:
            best_contain = notice_name
            break
    if best_contain:
        return 'near_contain', best_contain, 'distinctive-token subset match'
    return 'none', None, None


# ---------- Tests ----------

def threshold_clustering(spend, thresholds, skipped):
    out = {}
    rows_full = []
    full_bands = []
    for t in thresholds:
        value = t['value']
        low_incl = t['inclusive']
        band_lo, band_hi = 0.9 * value, value
        if low_incl:
            band = spend[(spend['Net amount'] >= band_lo) & (spend['Net amount'] < band_hi)]
        else:
            band = spend[(spend['Net amount'] >= band_lo) & (spend['Net amount'] <= band_hi)]
        comparator = spend[((spend['Net amount'] >= value) if low_incl else
                            (spend['Net amount'] > value)) & (spend['Net amount'] < 1.1 * value)]
        baseline = spend[(spend['Net amount'] >= 0.5 * value) & (spend['Net amount'] < 1.5 * value)]

        top_suppliers = (band[band['Supplier name'].str.upper() != 'REDACTED']
                          .groupby('supplier_norm').size().sort_values(ascending=False).head(20))
        by_tag = band.groupby('tag').agg(rows=('Net amount', 'size'), gbp=('Net amount', 'sum')).reset_index()
        top20 = band.sort_values('Net amount', ascending=False).head(20)

        out[str(value)] = {
            'threshold_value': value,
            'inclusive': low_incl,
            'rule_ids': t['rule_ids'],
            'competition_triggering': t['competition_triggering'],
            'band_90pct_to_threshold': {'count': int(len(band)), 'gbp': float(band['Net amount'].sum())},
            'comparator_band_threshold_to_110pct': {'count': int(len(comparator)), 'gbp': float(comparator['Net amount'].sum())},
            'wider_baseline_50pct_to_150pct': {'count': int(len(baseline)), 'gbp': float(baseline['Net amount'].sum())},
            'top20_suppliers_in_band': [{'supplier_norm': k, 'count': int(v)} for k, v in top_suppliers.items()],
            'by_tag': by_tag.to_dict(orient='records'),
            'parameters': {'lower_band_fraction': 0.9, 'comparator_upper_fraction': 1.1,
                           'baseline_lower_fraction': 0.5, 'baseline_upper_fraction': 1.5},
            'top20': top20[['row_id', 'Net amount', 'supplier_norm', 'tag', 'pay_date']].to_dict(orient='records'),
            'top20_rows_file': 'analytics-full/threshold_clustering_top20_rows.csv',
        }
        full_band = band.copy()
        full_band['threshold_value'] = value
        full_bands.append(full_band)
        band_top = band.sort_values('Net amount', ascending=False).head(20).copy()
        band_top['threshold_value'] = value
        rows_full.append(band_top[['row_id', 'threshold_value', 'Net amount', 'supplier_norm', 'Supplier name', 'tag', 'Service', 'Narrative', 'pay_date']])
    if rows_full:
        pd.concat(rows_full).to_csv(FULL / 'threshold_clustering_top20_rows.csv', index=False)
    else:
        pd.DataFrame().to_csv(FULL / 'threshold_clustering_top20_rows.csv', index=False)
    (pd.concat(full_bands) if full_bands else pd.DataFrame(columns=list(spend.columns)+['threshold_value'])).to_csv(FULL / 'threshold_clustering_full.csv', index=False)
    return out


def split_purchases(spend, thresholds, skipped):
    out = {}
    all_windows = []
    competition_thresholds = [t for t in thresholds if t['competition_triggering']]
    for t in competition_thresholds:
        value = t['value']
        windows_by_supplier = {}
        general = spend[spend['tag'] == 'general_procurement']
        placement = spend[spend['tag'] == 'care_or_education_placement']
        for scope_name, scope_df in (('all', spend),):
            below = scope_df[(scope_df['Net amount'] < value) & (scope_df['Supplier name'].str.upper() != 'REDACTED')]
            for supplier, grp in below.groupby('supplier_norm'):
                grp = grp.sort_values('pay_date')
                dates = pd.to_datetime(grp['pay_date'])
                # Payments on the same date define the exact same inclusive
                # window. Evaluate it once, preserving chronological tie order.
                for anchor_date in dates.drop_duplicates():
                    window_end = anchor_date + timedelta(days=30)
                    mask = (dates >= anchor_date) & (dates <= window_end)
                    window_rows = grp[mask.values]
                    if len(window_rows) < 2:
                        continue
                    total = window_rows['Net amount'].sum()
                    if total < value:
                        continue
                    key = supplier
                    existing = windows_by_supplier.get(key)
                    if existing is not None and total <= existing['total_gbp']:
                        continue
                    tag_gbp = window_rows.groupby('tag')['Net amount'].sum()
                    candidate = {
                        'supplier_norm': supplier,
                        'window_start': anchor_date.date().isoformat(),
                        'window_end': window_end.date().isoformat(),
                        'n_payments': int(len(window_rows)),
                        'distinct_amounts': int(window_rows['Net amount'].nunique()),
                        'total_gbp': float(total),
                        'window_total': float(total),
                        'dominant_tag': tag_gbp.sort_values(ascending=False).index[0],
                        'tag_gbp': tag_gbp.to_dict(),
                        'services': sorted(window_rows['Service'].unique().tolist()),
                        'tags': sorted(window_rows['tag'].unique().tolist()),
                        'row_ids': window_rows['row_id'].tolist(),
                    }
                    if existing is None or candidate['total_gbp'] > existing['total_gbp']:
                        windows_by_supplier[key] = candidate

        windows = list(windows_by_supplier.values())
        gp_windows = [w for w in windows if w['dominant_tag'] == 'general_procurement']
        placement_windows = [w for w in windows if w['dominant_tag'] == 'care_or_education_placement']

        def summarise(ws):
            return {
                'windows': len(ws),
                'distinct_suppliers': len({w['supplier_norm'] for w in ws}),
                'gbp': float(sum(w['total_gbp'] for w in ws)),
            }

        by_tag_rows = 0
        tag_totals = {}
        for w in windows:
            for tag in w['tags']:
                tt = tag_totals.setdefault(tag, {'windows': 0, 'gbp': 0.0})
                tt['windows'] += 1
                tt['gbp'] += w['tag_gbp'][tag]

        top20 = sorted(windows, key=lambda w: w['total_gbp'], reverse=True)[:20]
        out[str(value)] = {
            'threshold_value': value,
            'parameters': {'window_days': 30, 'minimum_payments': 2,
                           'deduplication': 'highest-total window per supplier and threshold; headlines use dominant tag by GBP'},
            'rule_ids': t['rule_ids'],
            'headline_general_procurement': summarise(gp_windows),
            'placement_separate': summarise(placement_windows),
            'all_windows': summarise(windows),
            'by_tag': tag_totals,
            'top20_windows': top20,
        }
        for i, w in enumerate(windows, 1):
            w['threshold_value'] = value
            w['window_id'] = f'W-{value}-{i:04d}'
        all_windows.extend(windows)
    pd.DataFrame(all_windows).to_csv(FULL / 'split_purchases_windows.csv', index=False)
    return out


def high_value_suppliers(spend, months_covered, thresholds, statutory_params):
    factor = 12 / months_covered
    agg = spend[spend['Supplier name'].str.upper() != 'REDACTED'].groupby('supplier_norm').agg(
        total_gbp=('Net amount', 'sum'), n_payments=('Net amount', 'size'),
        narrative=('Narrative', lambda s: s.value_counts().idxmax()),
        service=('Service', lambda s: s.value_counts().idxmax()),
        supplier_name=('Supplier name', 'first'),
        row_id=('row_id', 'first'),
    ).reset_index()
    agg['annualised_estimate'] = agg['total_gbp'] * factor

    tag_gbp = spend[spend['Supplier name'].str.upper() != 'REDACTED'].groupby(['supplier_norm', 'tag'])['Net amount'].sum().reset_index()
    dominant = tag_gbp.sort_values('Net amount', ascending=False).drop_duplicates('supplier_norm')[['supplier_norm', 'tag']]
    dominant = dominant.rename(columns={'tag': 'dominant_tag'})
    n_tags = tag_gbp.groupby('supplier_norm')['tag'].nunique().reset_index().rename(columns={'tag': 'n_tags'})
    agg = agg.merge(dominant, on='supplier_norm', how='left').merge(n_tags, on='supplier_norm', how='left')
    agg['spans_multiple_tags'] = agg['n_tags'] > 1

    competition_thresholds = [t for t in thresholds if t['competition_triggering']]
    lowest = min(competition_thresholds, key=lambda t: t['value']) if competition_thresholds else None

    skipped = []
    result = {'parameters': {}, 'by_tag': {}, 'headline_general_procurement': {}, 'tables': {}}
    agg.to_csv(FULL / 'high_value_suppliers_all.csv', index=False)

    if lowest is None:
        return {'skipped': True, 'reason': 'no competition-triggering threshold available'}, skipped, agg.iloc[:0], agg

    T = lowest['value']
    flagged = agg[agg['annualised_estimate'] >= T].copy()
    flagged.to_csv(FULL / 'high_value_suppliers_flagged.csv', index=False)

    by_tag = {}
    for tag, grp in flagged.groupby('dominant_tag'):
        by_tag[tag] = {'count': int(len(grp)), 'gbp_annualised': float(grp['annualised_estimate'].sum())}
    headline = flagged[flagged['dominant_tag'] == 'general_procurement'].sort_values('annualised_estimate', ascending=False)
    placement = flagged[flagged['dominant_tag'] == 'care_or_education_placement'].sort_values('annualised_estimate', ascending=False)
    grant = flagged[flagged['dominant_tag'] == 'grant'].sort_values('annualised_estimate', ascending=False)
    agency = flagged[flagged['dominant_tag'] == 'agency_staff'].sort_values('annualised_estimate', ascending=False)
    premises = flagged[flagged['dominant_tag'] == 'premises_non_procurement'].sort_values('annualised_estimate', ascending=False)

    cols = ['supplier_norm', 'supplier_name', 'annualised_estimate', 'total_gbp', 'n_payments',
            'narrative', 'service', 'dominant_tag', 'spans_multiple_tags', 'row_id']
    result = {
        'parameters': {
            'lowest_competition_triggering_threshold': T,
            'rule_ids': lowest['rule_ids'],
            'statutory_threshold_tier': 'skipped: STATUTORY_THRESHOLD_* parameters are null in rules.json',
        },
        'counts_and_gbp_by_dominant_tag': by_tag,
        'headline_general_procurement': {
            'count': int(len(headline)), 'gbp_annualised': float(headline['annualised_estimate'].sum()),
            'top20': headline[cols].head(20).to_dict(orient='records'),
        },
        'care_or_education_placement': {
            'count': int(len(placement)), 'gbp_annualised': float(placement['annualised_estimate'].sum()),
            'top20': placement[cols].head(20).to_dict(orient='records'),
        },
        'grant': {
            'count': int(len(grant)), 'gbp_annualised': float(grant['annualised_estimate'].sum()),
            'top20': grant[cols].head(20).to_dict(orient='records'),
        },
        'agency_staff': {
            'count': int(len(agency)), 'gbp_annualised': float(agency['annualised_estimate'].sum()),
            'top20': agency[cols].head(20).to_dict(orient='records'),
        },
        'premises_non_procurement': {
            'count': int(len(premises)), 'gbp_annualised': float(premises['annualised_estimate'].sum()),
            'top20': premises[cols].head(20).to_dict(orient='records'),
        },
        'full_flagged_file': 'analytics-full/high_value_suppliers_flagged.csv',
    }
    result['statutory_tiers']={}
    for name,param in statutory_params.items():
        if not name.startswith('STATUTORY_'):continue
        if param.get('value') is None:
            skipped.append({'test':'high_value_suppliers','tier':name,'reason':f'{name} is null in rules.json'})
            result['statutory_tiers'][name]={'skipped':True,'reason':f'{name} is null in rules.json'}
        else:
            tier=agg[agg['annualised_estimate']>=param['value']].sort_values('annualised_estimate',ascending=False)
            result['statutory_tiers'][name]={'threshold':param['value'],'count':len(tier),
                'gbp_annualised':float(tier['annualised_estimate'].sum()),'top20':tier[cols].head(20).to_dict(orient='records'),
                'limitation':'Supplier category cannot be inferred from spend; threshold screening is an exposure estimate, not a contract-route conclusion.'}
            tier.to_csv(FULL/f'high_value_{name.lower()}.csv',index=False)
    result['parameters']['statutory_threshold_tier']='see statutory_tiers; only auditor-supplied values are used'
    return result, skipped, flagged, agg


def publication_boundary(rules_doc):
    candidates = [r for r in rules_doc['rules'] if r.get('threshold_low') is not None
                  and 'publish a contract notice' in r.get('required_action', '').lower()]
    if not candidates:
        raise ValueError('No sourced publication boundary is available; do not classify notice absence.')
    low = min(r['threshold_low'] for r in candidates)
    rules = [r for r in candidates if r['threshold_low'] == low]
    return {'value': low, 'inclusive': any(r.get('threshold_low_inclusive') for r in rules),
            'rule_ids': [r['rule_id'] for r in rules]}


def off_contract(flagged, notices, contracts_present, register_present, publication_threshold=None):
    if not contracts_present and not register_present:
        return {'skipped': True, 'reason': 'no contracts.csv or contract register in data/'}, None

    publication_threshold = publication_threshold or publication_boundary(load_rules())
    active_notices = notices[notices['active'].astype(bool)]
    active_names = set(active_notices['supplier_norm'])
    spend_counts = {}
    for name in flagged['supplier_norm']:
        for tok in distinctive_tokens(name):
            spend_counts[tok] = spend_counts.get(tok, 0) + 1
    notice_counts = {}
    for name in active_names:
        for tok in distinctive_tokens(name):
            notice_counts[tok] = notice_counts.get(tok, 0) + 1

    matches = []
    for name in flagged['supplier_norm']:
        cls, candidate, rule = match_supplier(name, active_names, spend_counts, notice_counts)
        sources = active_notices.loc[active_notices['supplier_norm']==candidate,'source'] if 'source' in active_notices else pd.Series(['contracts_finder'])
        matches.append({'supplier_norm': name, 'match_class': cls, 'candidate_notice_supplier': candidate,
                        'candidate_source':';'.join(sorted(set(sources))) if candidate else '', 'match_rule': rule})
    match_df = pd.DataFrame(matches)
    merged = flagged.merge(match_df, on='supplier_norm', how='left')
    boundary = publication_threshold['value']
    merged['eligible_for_notice_test'] = (merged['annualised_estimate'] >= boundary if publication_threshold['inclusive']
                                         else merged['annualised_estimate'] > boundary)
    merged.to_csv(FULL / 'supplier-match.csv', index=False)

    near = merged[merged['match_class'].isin(['near_ratio', 'near_contain'])]
    near.to_csv(FULL / 'near-matches.csv', index=False)

    eligible = merged[merged['eligible_for_notice_test']]
    counts_by_class = eligible.groupby('match_class').agg(
        count=('supplier_norm', 'size'), gbp_annualised=('annualised_estimate', 'sum')).reset_index()

    # Near matches remain unconfirmed. They are never counted as covered.
    unmatched = eligible[eligible['match_class'] != 'exact']
    unmatched_by_tag = unmatched.groupby('dominant_tag').agg(
        count=('supplier_norm', 'size'), gbp_annualised=('annualised_estimate', 'sum')).reset_index()
    unmatched_gp = unmatched[unmatched['dominant_tag'] == 'general_procurement'].sort_values('annualised_estimate', ascending=False)
    cols = ['supplier_norm', 'supplier_name', 'annualised_estimate', 'total_gbp', 'n_payments',
            'narrative', 'service', 'dominant_tag'] + (['row_id'] if 'row_id' in merged else [])

    result = {
        'contracts_present': contracts_present,
        'register_present': register_present,
        'caveat': CAVEAT_TEXT,
        'parameters': {'publication_threshold': boundary, 'inclusive': publication_threshold['inclusive'],
                       'rule_ids': publication_threshold['rule_ids']},
        'eligible_supplier_count': int(len(eligible)),
        'below_publication_threshold_not_classified': int((~merged['eligible_for_notice_test']).sum()),
        'unconfirmed_definition': 'all eligible suppliers except exact matches; near names remain candidates',
        'counts_by_match_class': counts_by_class.to_dict(orient='records'),
        'unmatched_by_tag': unmatched_by_tag.to_dict(orient='records'),
        'unmatched_general_procurement_top20': unmatched_gp[cols].head(20).to_dict(orient='records'),
        'matching_summary_file': 'analytics-full/supplier-match.csv',
        'near_matches_file': 'analytics-full/near-matches.csv',
        'note': 'Only suppliers at or above the publication threshold are classed here; Contracts Finder does '
                'not carry smaller awards, so results must never be used to question smaller suppliers.',
    }
    match_counts = eligible['match_class'].value_counts().to_dict()
    return result, {k: int(v) for k, v in match_counts.items()}


def duplicates(spend):
    """All maximal seven-day windows, with overlap-safe row/value accounting.

    Windows may overlap so every qualifying pair remains visible. Each later
    payment is attributed to at most one group for the excess-value indicator.
    """
    non_redacted = spend[spend['Supplier name'].str.upper() != 'REDACTED'].copy()
    non_redacted['pay_date_dt'] = pd.to_datetime(non_redacted['pay_date'])
    all_groups = []
    for (supplier, amount), grp in non_redacted.groupby(['supplier_norm', 'Net amount']):
        if len(grp) < 2:
            continue
        grp = grp.sort_values(['pay_date_dt', 'Date', 'row_id'])
        dates = grp['pay_date_dt'].tolist()
        candidates = []
        for first in range(len(grp)):
            indices = tuple(i for i in range(first, len(grp)) if (dates[i]-dates[first]).days <= 7)
            if len(indices) >= 2:
                candidates.append(indices)
        maximal = [indices for indices in candidates
                   if not any(set(indices) < set(other) for other in candidates)]
        attributed = set()
        for indices in maximal:
            sub = grp.iloc[list(indices)]
            # The first row in the earliest window of each connected portion
            # is its baseline; later rows count once, even in overlapping windows.
            extras = set(sub['row_id'].iloc[1:]) - attributed
            attributed.update(extras)
            all_groups.append({
                'supplier_norm': supplier, 'amount': float(amount),
                'n_rows': int(len(sub)), 'gbp_beyond_first': float(amount * len(extras)),
                'tags': sorted(sub['tag'].unique().tolist()),
                'row_ids': sub['row_id'].tolist(), 'dates': sub['pay_date'].tolist(),
                'attributed_extra_row_ids': sorted(extras),
                'tier': 'same_timestamp' if sub['Date'].nunique() == 1 else 'different_time',
                'dominant_tag': sub.groupby('tag')['Net amount'].sum().sort_values(ascending=False).index[0],
            })
    out = {}
    for tier in ('same_timestamp', 'different_time'):
        groups = [g for g in all_groups if g['tier'] == tier]
        by_tag = {}
        for tag in sorted({g['dominant_tag'] for g in groups}):
            subset = [g for g in groups if g['dominant_tag'] == tag]
            by_tag[tag] = {'groups': len(subset),
                          'rows': len({rid for g in subset for rid in g['row_ids']}),
                          'gbp_beyond_first': sum(g['gbp_beyond_first'] for g in subset)}
        out[tier] = {
            'parameters': {'maximum_span_days': 7, 'tier': tier,
                'grouping': 'all maximal seven-day windows; windows may overlap; rows unique within tier; excess rows attributed once across windows'},
            'groups': len(groups), 'rows': len({rid for g in groups for rid in g['row_ids']}),
            'gbp_beyond_first_instance': float(sum(g['gbp_beyond_first'] for g in groups)),
            'by_tag': by_tag,
            'top20_groups': sorted(groups, key=lambda g:g['gbp_beyond_first'], reverse=True)[:20],
        }
    for i, group in enumerate(all_groups, 1):
        group['group_id'] = f'DUP-{i:04d}'
    pd.DataFrame(all_groups, columns=['group_id', 'supplier_norm', 'amount', 'n_rows',
        'gbp_beyond_first', 'tags', 'row_ids', 'dates', 'attributed_extra_row_ids', 'tier',
        'dominant_tag']).to_csv(FULL / 'duplicates.csv', index=False)
    return out


def expired_notice_spend(agg, notices, months_covered, rules_doc):
    ended = notices[notices['ended']]
    ended_names = set(ended['supplier_norm'])
    active_names = set(notices[notices['active']]['supplier_norm'])
    # suppliers whose EVERY matched notice ended before window start: exact match to ended set, and no active match
    candidates = agg[agg['supplier_norm'].isin(ended_names) & ~agg['supplier_norm'].isin(active_names)].copy()
    factor = 12 / months_covered
    candidates['annualised_estimate'] = candidates['total_gbp'] * factor
    detail = []
    for _, row in candidates.iterrows():
        matched = ended[ended['supplier_norm'] == row['supplier_norm']]
        latest_end = matched['contract_end'].max()
        notice_id = matched.sort_values('contract_end', ascending=False).iloc[0]['notice_id']
        detail.append({
            'supplier_norm': row['supplier_norm'], 'supplier_name': row['supplier_name'],
            'annualised_estimate': float(row['annualised_estimate']), 'total_gbp': float(row['total_gbp']),
            'latest_notice_end_date': latest_end, 'notice_id': notice_id,
        })
    detail_df = pd.DataFrame(detail).sort_values('annualised_estimate', ascending=False) if detail else pd.DataFrame(columns=['supplier_norm'])
    detail_df.to_csv(FULL / 'expired_notice_spend.csv', index=False)
    rule_d = [r['rule_id'] for r in rules_doc['rules'] if r['clause'].startswith('App C row D')]
    return {
        'count': int(len(detail_df)), 'gbp_annualised': float(detail_df['annualised_estimate'].sum()) if len(detail_df) else 0.0,
        'rule_ids': rule_d,
        'note': 'Indicator of spend after notice expiry without a documented extension; a newer contract may '
                'exist with no notice (contracts.csv is not a register).',
        'top20': detail_df.head(20).to_dict(orient='records'),
    }


def spend_vs_award(agg, notices, months_covered, rules_doc):
    active_counts = notices[notices['active']].groupby('supplier_norm')['notice_id'].nunique()
    ambiguous = set(active_counts[active_counts > 1].index)
    single_supplier_notices = notices.groupby('notice_id').filter(lambda g: g['suppliers_on_notice'].iloc[0] == 1)
    live = single_supplier_notices[single_supplier_notices['active'] & (single_supplier_notices['awarded_value'] > 0)].copy()
    live = live[~live['supplier_norm'].isin(ambiguous)]
    live = live.dropna(subset=['contract_start', 'contract_end'])
    live['contract_start_dt'] = pd.to_datetime(live['contract_start'])
    live['contract_end_dt'] = pd.to_datetime(live['contract_end'])
    live['contract_years'] = (live['contract_end_dt'] - live['contract_start_dt']).dt.days / 365.25
    live = live[live['contract_years'] > 0]
    live['award_annual_rate'] = live['awarded_value'] / live['contract_years']

    factor = 12 / months_covered
    agg2 = agg.copy()
    agg2['annualised_estimate'] = agg2['total_gbp'] * factor
    merged = agg2.merge(live[['supplier_norm', 'notice_id', 'awarded_value', 'contract_years', 'award_annual_rate']],
                         on='supplier_norm', how='inner')
    merged['ratio'] = merged['annualised_estimate'] / merged['award_annual_rate']
    flagged = merged[merged['ratio'] >= 1.25].sort_values('ratio', ascending=False)
    flagged.to_csv(FULL / 'spend_vs_award.csv', index=False)
    rule_e = [r['rule_id'] for r in rules_doc['rules'] if r['clause'].startswith('App C row E')]
    cols = ['supplier_norm', 'supplier_name', 'annualised_estimate', 'awarded_value', 'contract_years',
            'award_annual_rate', 'ratio', 'notice_id']
    return {
        'count': int(len(flagged)), 'rule_ids': rule_e,
        'parameters': {'indicator_ratio': 1.25, 'days_per_year': 365.25,
                       'allocation': 'one active notice per supplier, single-supplier, positive award and valid term'},
        'excluded_multiple_active_notice_suppliers': int(agg['supplier_norm'].isin(ambiguous).sum()),
        'caveat': 'Award values may be estimates or maxima; ratio >= 1.25 is an indicator to confirm, not evidence of a variation.',
        'top20': flagged[cols].head(20).to_dict(orient='records'),
    }


def main():
    rules_doc = load_rules()
    thresholds, skipped_params = build_thresholds(rules_doc)

    spend = pd.read_csv(FULL / 'spend-clean.csv')
    spend['pay_date'] = pd.to_datetime(spend['pay_date']).dt.date
    cleaning_log = json.loads((FULL / 'cleaning-log.json').read_text())
    months_covered = cleaning_log['months_covered']
    contracts_log = cleaning_log['contracts']
    contracts_present = contracts_log['contracts_present']
    register_present = cleaning_log['register']['register_present']

    if contracts_present:
        notices = pd.read_csv(FULL / 'notices-clean.csv')
    else:
        notices = pd.DataFrame(columns=['supplier_norm', 'active', 'ended', 'notice_id', 'contract_end',
                                         'awarded_value', 'suppliers_on_notice', 'contract_start'])

    skipped = []
    for sp in skipped_params:
        skipped.append({'test': 'threshold_clustering/split_purchases/high_value_suppliers', **sp})

    tc = threshold_clustering(spend, thresholds, skipped)
    sp_result = split_purchases(spend, thresholds, skipped)
    hv_result, hv_skipped, flagged, agg = high_value_suppliers(spend, months_covered, thresholds, rules_doc['parameters'])
    skipped.extend(hv_skipped)

    match_sources=notices
    if register_present:
        register=pd.read_csv(FULL/'register-clean.csv')
        match_sources=pd.concat([notices,register],ignore_index=True)
    oc_result, oc_match_counts = off_contract(agg, match_sources, contracts_present, register_present,
                                             publication_threshold=publication_boundary(rules_doc))
    if isinstance(oc_result, dict) and oc_result.get('skipped'):
        skipped.append({'test': 'off_contract', **oc_result})

    dup_result = duplicates(spend)

    if contracts_present:
        exp_result = expired_notice_spend(agg, notices, months_covered, rules_doc)
        sva_result = spend_vs_award(agg, notices, months_covered, rules_doc)
    else:
        exp_result = {'skipped': True, 'reason': 'contracts.csv not present'}
        sva_result = {'skipped': True, 'reason': 'contracts.csv not present'}
        skipped.append({'test': 'expired_notice_spend', 'reason': 'contracts.csv not present'})
        skipped.append({'test': 'spend_vs_award', 'reason': 'contracts.csv not present'})

    tags_summary = cleaning_log['tags']

    analytics = {
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'scripts': ['scripts/clean.py', 'scripts/analyse.py'],
        'population': {
            'files': cleaning_log['spend_files'],
            'rows_raw': cleaning_log['rows_raw'],
            'rows_after_exclusions': cleaning_log['rows_after_exclusions'],
            'date_min': cleaning_log['date_min'],
            'date_max': cleaning_log['date_max'],
            'months_covered': months_covered,
            'annualisation_factor': 12 / months_covered,
            'total_gbp': cleaning_log['total_gbp_after_exclusions'],
            'excluded': cleaning_log['exclusions'],
            'tags': tags_summary,
            'limitations': [
                'population is expenditure over £500 only; split-purchase and duplicate results are lower bounds',
                'Date is a payment-run timestamp, not an invoice date; many rows share one timestamp',
                'Redacted supplier rows (~1/5 of rows) are excluded from every supplier-level test',
                'Rule bands apply to total contract values, not individual net payments or a supplier run-rate; tests are screening indicators only',
                'Clause 6.15 includes VAT in total contract value while Appendix B says exclusive of VAT; the source conflict is not resolved',
                'Scope/category cannot be inferred from supplier names; shared threshold bands are exploratory and preserve all rule-specific boundaries',
                'Active notice matching follows the guide end-date screen; it does not prove a contract covered the particular payment or service',
            ],
        },
        'thresholds': thresholds,
        'skipped': skipped,
        'contracts': contracts_log,
        'matching': {
            **{k: 0 for k in ('exact', 'near_ratio', 'near_contain', 'none')},
            **(oc_match_counts or {}),
            'near_matches_file': 'analytics-full/near-matches.csv',
        },
        'tests': {
            'threshold_clustering': tc,
            'split_purchases': sp_result,
            'high_value_suppliers': hv_result,
            'off_contract': oc_result,
            'duplicates': dup_result,
            'expired_notice_spend': exp_result,
            'spend_vs_award': sva_result,
        },
    }

    with (ROOT / 'outputs' / 'analytics.json').open('w') as fh:
        json.dump(analytics, fh, indent=2, default=str)

    print('analyse.py complete')
    print(f"thresholds derived: {[t['value'] for t in thresholds]}")
    print(f"skipped tiers: {len(skipped)}")


if __name__ == '__main__':
    main()
