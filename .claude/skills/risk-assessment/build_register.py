"""Resolve evidence and build a risk register; never supplies human decisions.

Run from the repository: .venv/bin/python .claude/skills/risk-assessment/build_register.py
--root permits isolated fixtures. Validation failure leaves the last valid register intact.
"""
import argparse
import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

TAG = re.compile(r'\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]')
PLACEHOLDER = re.compile(r'\{\{([^{}]+)\}\}')
PATH = re.compile(r'\$(?:\.[^.\[\]]+|\[\d+\])*')
FIELDS = ('id', 'title', 'risk', 'likelihood', 'impact', 'evidence',
          'proposed_focus', 'recommend_in_scope', 'sample_source')
ADVERSE = re.compile(r'limited|weak|no assurance|unsatisfactory|inadequate', re.I)

STATE_FILES = {'rules':'rules.json', 'analytics':'analytics.json', 'history':'history.json',
               'ratings':'risk-ratings.json', 'register':'risk-register.md',
               'comments':'auditor-comments.md', 'baseline':'risk-baseline.json'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_approval_state(state_path, paths=None):
    """A version binding, not an authentication signature or human decision."""
    state_path = Path(state_path)
    errors = []
    try:
        state = json.loads(state_path.read_text())
        if not state.get('validated') or not state.get('all_decided') or not state.get('revision'):
            errors.append('gate: no successfully validated human-decision revision')
        if state.get('validator_sha256') != sha(__file__):
            errors.append('gate: register validator changed; rebuild the register')
        if state.get('method_sha256') != sha(Path(__file__).with_name('SKILL.md')):
            errors.append('gate: assessment method changed; rebuild the register')
        if set(state.get('files', {})) != set(STATE_FILES):
            errors.append('gate: incomplete validated file binding')
        for name, item in state.get('files', {}).items():
            path = Path(paths[name]).resolve() if paths else (state_path.parent/item['path']).resolve()
            if not path.is_relative_to(state_path.parent.resolve()):
                errors.append(f'gate: {name} outside validated output directory')
            elif not path.is_file() or sha(path) != item['sha256']:
                errors.append(f'gate: {name} changed since register validation; rebuild with current decisions')
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f'gate: missing/malformed validated approval state: {error}')
    return errors


def jpath(doc, path):
    if not isinstance(path, str) or not PATH.fullmatch(path):
        raise ValueError(f'invalid complete JSON path: {path}')
    value = doc
    for name, index in re.findall(r'\.([^.\[\]]+)|\[(\d+)\]', path[1:]):
        if index:
            if not isinstance(value, list):
                raise ValueError(f'not a list in {path}')
            value = value[int(index)]
        else:
            if not isinstance(value, dict):
                raise ValueError(f'not an object in {path}')
            value = value[name]
    return value


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def fmt(value):
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return 'not supplied'
    if isinstance(value, (dict, list)):
        raise ValueError('placeholder must refer to a scalar')
    if isinstance(value, int):
        return f'{value:,}'
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('non-finite metric')
        return f'{value:,.2f}' if not value.is_integer() else f'{int(value):,}'
    return str(value)


def cell(value):
    return str(value).replace('|', '&#124;').replace('\n', ' ')


def decisions(path):
    result = {'reviewer': '', 'date': '', 'rows': {}}
    if not path.exists():
        return result
    text = path.read_text()
    for field in ('reviewer', 'date'):
        found = re.search(rf'^{field.title()}:[ \t]*(.*)$', text, re.M)
        result[field] = found.group(1).strip() if found else ''
    for line in text.splitlines():
        cols = [c.strip().replace('&#124;', '|') for c in line.strip().strip('|').split('|')]
        if len(cols) >= 6 and re.fullmatch(r'R-\d+', cols[0]):
            if cols[0] in result['rows']:
                raise ValueError(f'duplicate decision row {cols[0]}')
            result['rows'][cols[0]] = dict(zip(('title', 'now', 'scope', 'decision', 'comment'), cols[1:6]))
            result['rows'][cols[0]]['decision'] = cols[4].lower()
    return result


def set_field(value, path, new_value):
    parts = path.split('.')
    if parts[0] not in FIELDS or parts[0] == 'id':
        raise ValueError(f'amendment field not allowed: {path}')
    target = value
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = new_value


def check_revision(ratings, baseline, dec, errors):
    """Compare exact snapshots; free-text amendments need structured instructions.

    Structured amendment JSON is placed by the human (or transcribed from their
    explicit instruction) in the Comment cell. The model cannot authorise itself.
    """
    active = any(row['decision'] for row in dec['rows'].values())
    if not active:
        if ratings.get('revision'):
            errors.append('revision supplied without actual auditor decisions')
        return False
    old = {r['id']: r for r in baseline.get('risks', [])}
    new = {r['id']: r for r in ratings.get('risks', [])}
    excluded = {r.get('id'): r for r in ratings.get('excluded', [])}
    revision = ratings.get('revision', {})
    number = revision.get('number')
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        errors.append('actual decisions require a numbered revision')
    changes = revision.get('changes', [])
    changes_by_id = {r.get('id'): r.get('action') for r in changes}
    if len(changes_by_id) != len(changes):
        errors.append('duplicate IDs in revision changes')
    expected_changes = {}
    if not old and not baseline.get('excluded'):
        errors.append('revision has no previously validated risk baseline')
    if set(new) - set(old):
        errors.append('new risks require explicit auditor instructions and a reviewed new baseline')
    for rid, before in old.items():
        row = dec['rows'].get(rid, {})
        decision = row.get('decision', '')
        if decision == '':
            if new.get(rid) != before:
                errors.append(f'{rid}: undecided risk changed without auditor instruction')
        elif decision not in ('approve', 'amend', 'reject'):
            errors.append(f'{rid}: missing or invalid auditor decision')
        elif decision == 'approve':
            if new.get(rid) != before:
                errors.append(f'{rid}: approved risk changed')
        elif decision == 'reject':
            expected_changes[rid] = 'rejected'
            reason = row.get('comment', '').strip()
            if rid in new or not reason or excluded.get(rid, {}).get('reason') != reason:
                errors.append(f'{rid}: rejection must remove the risk and preserve the exact auditor reason')
        else:
            expected_changes[rid] = 'amended'
            try:
                request = json.loads(row.get('comment', ''))
                if not isinstance(request, dict) or not request:
                    raise ValueError('nonempty JSON object required')
                for dimension in ('likelihood', 'impact'):
                    if any(k in request for k in (f'{dimension}.score', f'{dimension}.base_score')) and f'{dimension}.justification' not in request:
                        errors.append(f'{rid}: score amendment must include its corresponding cited justification')
                wanted = copy.deepcopy(before)
                for field, value in request.items():
                    if field == 'auditor_override':
                        wanted[field] = value
                    else:
                        set_field(wanted, field, value)
                if new.get(rid) != wanted:
                    errors.append(f'{rid}: amendment not applied exactly or unrequested field changed')
            except (ValueError, KeyError, TypeError) as error:
                errors.append(f'{rid}: amendment Comment must specify exact JSON field changes: {error}')
    prior_excluded = {x.get('id'):x for x in baseline.get('excluded', []) if x.get('id')}
    for rid in set(dec['rows']).intersection(prior_excluded):
        row = dec['rows'][rid]
        if row['decision'] != 'reject' or excluded.get(rid, {}).get('reason') != row['comment']:
            errors.append(f'{rid}: changing a previously rejected risk requires explicit reviewed reinstatement')
        expected_changes[rid] = 'rejected'
    # Recheck after including any rejection preserved from a previous revision.
    if changes_by_id != expected_changes and 'revision changes do not exactly match amended/rejected decisions' not in errors:
        errors.append('revision changes do not exactly match amended/rejected decisions')
    unknown = set(dec['rows']) - set(old) - set(prior_excluded)
    if unknown:
        errors.append(f'decision IDs outside validated baseline: {sorted(unknown)}')
    return True


def council_rating(history, likelihood, impact):
    method = history.get('scoring_method', {})
    score = likelihood * impact
    if not method.get('usable'):
        label = ('Very low', 'Low', 'Medium', 'High', 'Very high')[max(likelihood, impact)-1]
        return score, label, f'Fallback {label}'
    cells = method['combination']['matrix_cells']
    matching = [c for c in cells if c['likelihood'] == likelihood and c['impact'] == impact]
    if len(matching) != 1 or matching[0]['score'] != score:
        raise ValueError('council matrix cell missing, duplicated or inconsistent with product')
    for band in method['bands']:
        nums = [int(n) for n in re.findall(r'\d+', band['score_range'])]
        lo, hi = (1, nums[0]) if len(nums) == 1 else nums
        if lo <= score <= hi:
            return score, matching[0]['label'], band['level']
    raise ValueError(f'no printed council band covers attainable score {score}')


def build(root):
    root = Path(root)
    out = root / 'outputs'
    result = {'errors': [], 'warnings': [], 'kept_ids': [], 'dropped': []}
    errors, warnings = result['errors'], result['warnings']
    try:
        rules_doc, analytics, history, ratings = [json.loads((out / f'{name}.json').read_text())
            for name in ('rules', 'analytics', 'history', 'risk-ratings')]
        dec = decisions(out / 'auditor-comments.md')
        baseline_path = out / 'risk-baseline.json'
        baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
        revised = check_revision(ratings, baseline, dec, errors)
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f'missing/malformed input: {error}')
        return result
    rules = {r['rule_id']: r for r in rules_doc['rules']}
    history_ids = {r['id']: r for r in walk(history) if isinstance(r.get('id'), str)}
    used = {}

    def resolve(kind, key):
        if kind == 'rule':
            value = rules[key]
        elif kind == 'metric':
            value = jpath(analytics, key)
        else:
            value = jpath(history, key) if key.startswith('$') else history_ids[key]
            if not isinstance(value, dict) or not all(k in value for k in ('source', 'pdf_page', 'quote')):
                raise ValueError(f'history citation is not a sourced item: {key}')
        used[(kind, key)] = value
        return value

    def text_check(text, where, must_cite=False):
        if not isinstance(text, str) or not text.strip():
            errors.append(f'{where}: missing text')
            return ''
        found = TAG.findall(text)
        if must_cite and not found:
            errors.append(f'{where}: justification has no resolvable citation')
        for kind, key in found:
            try:
                resolve(kind, key)
            except (KeyError, ValueError, IndexError, TypeError) as error:
                errors.append(f'{where}: unresolved {kind}:{key}: {error}')
        stripped = TAG.sub('', text)
        for path in PLACEHOLDER.findall(text):
            try:
                value = jpath(analytics, path)
                fmt(value)
                used[('metric',path)] = value
            except (KeyError, ValueError, IndexError, TypeError) as error:
                errors.append(f'{where}: invalid scalar placeholder {path}: {error}')
        if re.search(r'\d|[£$€]', PLACEHOLDER.sub('', stripped)):
            warnings.append(f'{where}: literal figure/currency in prose; replace with a metric placeholder')
        if '{{' in PLACEHOLDER.sub('', text) or '}}' in PLACEHOLDER.sub('', text):
            errors.append(f'{where}: malformed placeholder')
        return text

    kept = []
    ids = set()
    for risk in ratings.get('risks', []):
        start = len(errors)
        rid = risk.get('id', '?')
        if not re.fullmatch(r'R-\d+', rid) or rid in ids:
            errors.append(f'{rid}: invalid/duplicate risk ID')
        ids.add(rid)
        for field in FIELDS:
            if field not in risk:
                errors.append(f'{rid}: missing {field}')
        like, imp = risk.get('likelihood', {}), risk.get('impact', {})
        for field, value in [('base likelihood', like.get('base_score')), ('likelihood', like.get('score')), ('impact', imp.get('score'))]:
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
                errors.append(f'{rid}: {field} must be an integer from one to five')
        for field in ('title', 'risk', 'proposed_focus'):
            text_check(risk.get(field), f'{rid}.{field}')
        text_check(like.get('justification'), f'{rid}.likelihood', True)
        text_check(imp.get('justification'), f'{rid}.impact', True)
        for index, text in enumerate(risk.get('evidence', [])):
            text_check(text, f'{rid}.evidence[{index}]', True)
        if not isinstance(risk.get('recommend_in_scope'), bool):
            errors.append(f'{rid}: recommend_in_scope must be boolean')
        repeat = like.get('repeat_audit_id')
        if repeat:
            audit = history_ids.get(repeat, {})
            if audit not in history.get('audits', []) or not ADVERSE.search(audit.get('opinion', '')):
                errors.append(f'{rid}: repeat uplift needs a cited audit with an adverse opinion')
            if f'[history:{repeat}]' not in like.get('justification', ''):
                errors.append(f'{rid}: repeat audit must be cited in likelihood justification')
        base, likelihood = like.get('base_score'), like.get('score')
        if isinstance(base, int) and likelihood != min(5, base + bool(repeat)) and not risk.get('auditor_override'):
            errors.append(f'{rid}: likelihood does not match base plus the single repeat uplift')
        if risk.get('auditor_override'):
            row = dec['rows'].get(rid, {})
            if row.get('decision') != 'amend' or not revised:
                errors.append(f'{rid}: auditor override requires an actual amendment')
        source = risk.get('sample_source', '')
        if source:
            base_dir = (out / 'analytics-full').resolve()
            candidate = (base_dir / source).resolve()
            if not candidate.is_relative_to(base_dir) or not candidate.is_file():
                errors.append(f'{rid}: sample_source must name an existing file within analytics-full')
        if len(errors) == start:
            try:
                score, label, band = council_rating(history, likelihood, imp['score'])
                kept.append((risk, score, label, band))
                result['kept_ids'].append(rid)
            except (KeyError, ValueError, TypeError) as error:
                errors.append(f'{rid}: {error}')
        if len(errors) > start:
            result['dropped'].append({'id': rid, 'reason': '; '.join(errors[start:])})
    if not kept and not revised:
        errors.append('no valid rated risk')
    # All failure diagnostics are retained; neither decisions nor validated outputs
    # are changed when citations, revisions or prose fail the build.
    (out / 'risk-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    if errors or warnings:
        return result

    def render(text):
        return PLACEHOLDER.sub(lambda match: fmt(jpath(analytics, match.group(1))), text)

    method = history.get('scoring_method', {})
    lines = ['# Procurement audit risk register', '']
    if revised:
        changed = ', '.join(f"{c['id']} {c['action']}" for c in ratings['revision'].get('changes', [])) or 'approved risks unchanged'
        lines += [f"*Revision {ratings['revision']['number']}, following auditor comments: {changed}.*", '']
    lines += ['Status: risk assessment and auditor scope decisions; indicators are not findings of non-compliance.', '']
    if method.get('usable'):
        matrix = method['combination']; band = method['bands'][0]
        lines += [f"Method: the council's likelihood and impact scales, Figure 1 matrix ({matrix['source']}, PDF p.{matrix['pdf_page']}) and Table 4 response bands (PDF p.{band['pdf_page']}). Python computes likelihood × impact and looks up both printed labels.", '',
                  'Source discrepancies retained: Table 1 / Figure 1 use Medium impact at three although the introductory prose prints two; Figure 1 calls the middle upper band High while Table 4 calls it Medium–High. Table 4 controls the response band. Figure 4 separately places scores of nine or above on the Corporate Risk Register, while the adjacent prose and Table 4 describe escalation of Extreme risks. That different Figure 4 rule is disclosed, not silently substituted.', '',
                  'The financial percentage bands overlap in the source. No inferred budget, loss estimate or probability is calculated from payment totals. Impact is an explicit consequence scenario using the printed descriptors; likelihood is a consistent planning judgment under the skill rubric, not a measured event probability.', '']
    else:
        lines += ['Fallback declared: history reports no usable council scoring method. Use likelihood/impact one to five (Very low to Very high); product is a prioritisation score and no council escalation is asserted.', '']
    lines += ['## Summary', '', '| ID | Risk | L | I | Score | Matrix label | Response band | Proposed focus | Scope |', '|---|---|---:|---:|---:|---|---|---|---|']
    for risk, score, label, band in kept:
        lines.append('| ' + ' | '.join(map(cell, [risk['id'], risk['title'], risk['likelihood']['score'], risk['impact']['score'], score, label, band, risk['proposed_focus'], 'In' if risk['recommend_in_scope'] else 'Out'])) + ' |')
    for risk, score, label, band in kept:
        lines += ['', f"## {risk['id']}: {risk['title']}", '', render(risk['risk']), '',
                  f"Likelihood ({risk['likelihood']['score']}): {render(risk['likelihood']['justification'])}", '',
                  f"Impact ({risk['impact']['score']}): {render(risk['impact']['justification'])}", '']
        if risk.get('auditor_override'):
            lines += ['**Auditor override applied; the requested judgment overrides the model recommendation.**', '']
        lines += ['Evidence:'] + [f'- {render(text)}' for text in risk['evidence']]
        lines += ['', f"Proposed focus: {render(risk['proposed_focus'])}", f"Sample source: `{risk['sample_source']}`" if risk['sample_source'] else 'Sample source: document/enquiry test; no transaction sample assumed.']
    lines += ['', '## Excluded themes', '']
    for item in ratings.get('excluded', []):
        lines.append(f"- {item.get('id') or item.get('theme', 'Theme')}: {item['reason']}")
    if not ratings.get('excluded'):
        lines.append('None.')
    lines += ['', '## Source references', '']
    for (kind, key), value in sorted(used.items()):
        if kind == 'rule':
            lines.append(f"- [rule:{key}] clause {value['clause']}, PDF p.{value['page']}: “{value['verbatim_quote']}”")
        elif kind == 'history':
            lines.append(f"- [history:{key}] {value['source']}, PDF p.{value['pdf_page']}: “{value['quote']}”")
        else:
            description = fmt(value) if not isinstance(value, (dict, list)) else 'named summary collection in analytics.json'
            lines.append(f'- [metric:{key}] analytics.json: {description}')
    lines += ['', '## Auditor decisions', '']
    if revised:
        for rid, row in dec['rows'].items():
            if row['decision']:
                lines.append(f"- {rid}: {row['decision']}; {row['comment'] or 'approved without amendment'}. Applied in this revision.")
            else:
                lines.append(f'- {rid}: undecided; kept unchanged pending auditor decision.')
    else:
        lines.append('None recorded. The auditor must record approve, amend or reject for each risk in auditor-comments.md. A blank cell means no decision.')
    (out / 'risk-register.md').write_text('\n'.join(lines) + '\n')
    rows = dict(dec['rows'])
    for risk, score, label, band in kept:
        prior = rows.get(risk['id'], {})
        rows[risk['id']] = {'title': risk['title'], 'now': f"{score} / {band}", 'scope': 'In' if risk['recommend_in_scope'] else 'Out', 'decision': prior.get('decision', ''), 'comment': prior.get('comment', '')}
    comments = ['# Auditor scope decisions', '', f"Reviewer: {dec['reviewer']}", f"Date: {dec['date']}", '',
                'A blank Decision cell means no decision. Use approve, amend or reject. Rejection requires a reason. For an amendment, record exact field changes as JSON in Comment, for example {"recommend_in_scope": false}; a score change must also include its cited justification. The assistant may transcribe your explicit instructions, and may never authorise a decision.', '',
                '| ID | Risk | Current rating | Scope | Decision | Comment |', '|---|---|---|---|---|---|']
    for rid, row in rows.items():
        comments.append('| ' + ' | '.join(map(cell, [rid, row['title'], row['now'], row['scope'], row['decision'], row['comment']])) + ' |')
    (out / 'auditor-comments.md').write_text('\n'.join(comments) + '\n')
    # The next review starts from this successfully rendered version. Old
    # versions remain available in version control and the execution evidence.
    baseline_path.write_text(json.dumps(ratings, indent=2) + '\n')
    final_decisions = decisions(out/'auditor-comments.md')
    state = {'validated':True, 'revision':ratings.get('revision',{}).get('number'),
             'all_decided':bool(final_decisions['rows']) and all(r['decision'] for r in final_decisions['rows'].values()),
             'validator_sha256':sha(__file__), 'method_sha256':sha(Path(__file__).with_name('SKILL.md')),
             'files':{name:{'path':filename,'sha256':sha(out/filename)} for name,filename in STATE_FILES.items()}}
    (out/'risk-approval-state.json').write_text(json.dumps(state,indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    result = build(args.root)
    for kind in ('errors', 'warnings'):
        for item in result[kind]:
            print(('FAIL' if kind == 'errors' else 'WARN') + ' ' + item)
    print(f"Valid risks: {len(result['kept_ids'])}; dropped: {len(result['dropped'])}")
    if result['errors'] or result['warnings']:
        return 1
    print('ALL CHECKS PASSED; register and decision template written. No human approval supplied by this program.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
