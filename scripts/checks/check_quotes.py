#!/usr/bin/env python3
"""QA check: every quote exists in its source.

1. Runs the extract-rules verifier: every verbatim_quote in outputs/rules.json
   is found in data/contract-rules.pdf on its stated page.
2. Every rule quote excerpt printed in outputs/risk-register.md
   ("- [rule:CPR-xx] clause ... : "...") is the start of that rule's quote.
Prints PASS/FAIL lines and a summary; exit 0 when clean.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / ".claude/skills/extract-rules/verify_quotes.py"
RULES = ROOT / "outputs/rules.json"
PDF = ROOT / "data/contract-rules.pdf"
REGISTER = ROOT / "outputs/risk-register.md"


def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()


def check_register_excerpts(text, rules):
    failures, count = [], 0
    for line in text.splitlines():
        if not line.startswith('- [rule:'):
            continue
        match = re.fullmatch(r'- \[rule:(CPR-\d+)\] clause [^:]+: ["“](.*?)(…?)["”]\s*',line)
        if not match:
            failures.append('register source-reference line could not be checked: '+line[:100])
            continue
        rid,excerpt=match.group(1),match.group(2)
        count+=1
        if rid not in rules:
            failures.append(f'register cites unknown rule {rid}')
        elif not norm(rules[rid]['verbatim_quote']).startswith(norm(excerpt)):
            failures.append(f'register excerpt for {rid} does not match rules.json')
    return count,failures


def main():
    fails = []
    if not VERIFIER.exists():
        fails.append(f"verifier missing: {VERIFIER}")
    else:
        p = subprocess.run([sys.executable, str(VERIFIER), str(RULES), str(PDF)], capture_output=True, text=True)
        last = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
        print(f"verify_quotes.py: exit {p.returncode}: {last}")
        if p.returncode != 0:
            fails.append("verify_quotes.py reported failures: " + last)
    rules = {r["rule_id"]: r for r in json.loads(RULES.read_text())["rules"]}
    n_excerpts = 0
    if REGISTER.exists():
        n_excerpts,excerpt_failures=check_register_excerpts(REGISTER.read_text(encoding='utf-8'),rules)
        fails.extend(excerpt_failures)
        if not n_excerpts:fails.append('risk register contains no verifiable rule source references')
    else:
        fails.append('risk-register.md missing')
    print(f"register excerpts checked: {n_excerpts}")
    for f in fails:
        print("FAIL ", f)
    print(f"SUMMARY quotes: rules={len(rules)} register_excerpts={n_excerpts} failures={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
