# Procurement Audit Planner

[Open the web application](https://procurement-audit-planner.onrender.com/) · [Setup and deployment](docs/web-application.md)

[View a completed example](https://procurement-audit-planner.onrender.com/example/) to inspect a real signed review, its working papers and four passed checks without starting a new run.

This repository contains the complete Skills + Agents implementation, web backend, interface, deployment configuration and signed planning papers.

A Skills + Agents system for planning a procurement audit of West Berkshire Council using the supplied public documents and payment data. It extracts procurement rules, analyses payments, incorporates audit history and produces an audit plan for human approval. Its outputs identify indicators to investigate, rather than findings of non-compliance.

**Included signed plan:** seven approved risks, ten controls, eleven audit tests and eleven client-document requests. The planner, challenger and QA reviewer completed two review rounds and resolved three issues. All four final checks pass, and Jay Yu signed off the plan on 15 October 2026.

## Skills and agents

| Skill | Purpose |
|---|---|
| `extract-rules` | Extract testable rules and exact source quotes from the procurement rules PDF. |
| `risk-assessment` | Combine rules, payment indicators and audit history into cited risk ratings. |
| `audit-program` | Turn approved risks into controls, tests, sample recipes and client-document requests. |

Skills are defined in `.claude/skills/`; agent definitions are in `.claude/agents/`.

| Agent | Responsibility |
|---|---|
| `spend-analyst` | Clean the payment files, run seven analyses and check their calculations. |
| `findings-analyst` | Extract prior audit opinions, coverage and the council's risk-scoring method. |
| `risk-assessor` | Produce the risk register for the auditor's scope decision. |
| `planner` | Build the approved audit plan and respond to review points. |
| `challenger` | Challenge control coverage, tests and sampling; verify accepted changes. |
| `qa-reviewer` | Run the four checks and report whether the plan is ready for sign-off. |

The workflow is: **rules and audit history → payment analysis → risk register → human scope approval → planning team → QA → human sign-off**. The planning agents exchange challenges and responses directly. Python computes figures, scores and samples; the agents interpret evidence and design tests.

## Final outputs

| File | Contents |
|---|---|
| [Risk register](outputs/risk-register.md) | Risk ratings, evidence and proposed focus. |
| [Scope decisions](outputs/auditor-comments.md) | The auditor's decisions for all seven risks. |
| [Planning memo](outputs/planning-memo.md) | Purpose, scope, approach, coverage and limitations. |
| [Risk-control matrix](outputs/risk-control-matrix.md) | Risks linked to expected controls and tests. |
| [Audit program](outputs/audit-program.md) | Fieldwork steps, payment samples and client-document requests. |
| [Review points](outputs/challenges.md) | Three resolved challenges and the planner's responses. |
| [QA and sign-off](outputs/review.md) | Final check results and the auditor's sign-off. |

The ten [sample CSVs](outputs/samples/) contain 267 test-payment occurrences representing **236 unique payments**. Reuse across tests does not increase unique coverage. Selections from client case and award records are specified for future fieldwork and are not included in those counts.

## Run and verify

Requirements: Python 3.10+, the packages in `requirements.txt`, and Poppler's `pdftotext` and `pdfinfo` on PATH.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-web.txt
.venv/bin/python scripts/clean.py
.venv/bin/python scripts/analyse.py
.venv/bin/python scripts/selfcheck.py
.venv/bin/python .claude/skills/risk-assessment/build_register.py
.venv/bin/python .claude/skills/audit-program/build_pack.py --gate
.venv/bin/python .claude/skills/audit-program/build_pack.py
.venv/bin/python scripts/checks/run_checks.py
.venv/bin/python -m pytest -q
```

These commands reproduce the calculations and build from the included judgments and approvals. To regenerate model judgments, follow `CLAUDE.md`: run `/extract-rules`, the analytical subagents and the risk assessor; obtain human scope decisions; then start `planner`, `challenger` and `qa-reviewer` with the [team prompt](docs/interactive-team-prompt.txt). Final verification covers source quotes, figures, traceability and samples. The test suite covers the analytical tools and web workflow.

**Verification refreshed 16 October 2026:** 164 tests passed with Python 3.12 and Poppler; all four Part A audit checks passed. A fresh public-hosted test completed model assessment, scope decisions, planning, QA, test-only sign-off and ZIP download. See [verification evidence](evidence/web-checks.txt). Grading-period hosting expiry and remaining account allowances still require confirmation by the deployment owner.

## Data and limitations

The supplied workbooks contain 10,607 payment rows for May–July 2026. After documented exclusions, 8,534 payments totalling £66,778,104.78 remain. Original inputs are preserved in `data/`, with [source checksums](evidence/source-manifest.json). Analytical summaries are in `outputs/analytics.json`; full lists are in `outputs/analytics-full/`.

Payments are published only above £500; payment-run dates are not invoice dates. Supplier totals and annualisation do not establish contract value or loss. Contracts Finder is incomplete and is not the council's contract register. Missing statutory parameters, source VAT/boundary ambiguities and risk-scoring discrepancies are disclosed. Grants remain tagged in the data, but separate grant-only fieldwork is outside the approved scope. Targeted samples do not support statistical population conclusions.

## Course requirements and sources

The guide's building, analysis, approval, team-review and sign-off steps are completed; see the [completion checklist](docs/guide-completion.md). The included papers record the signed planning workflow. Each web review generates its own risk assessment and planning pack.

- [Assignment requirements](https://bruinlearn.ucla.edu/courses/237935/assignments/2055518)
- [Course guide](https://procurement-audit-planner.vercel.app/)
- [Source attribution](docs/source-attribution.md)
