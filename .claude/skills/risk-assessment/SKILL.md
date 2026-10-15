---
name: risk-assessment
description: Merge the verified rules, spend indicators and sourced history into a cited risk register, using the council's matrix and a real human decision gate.
---

# risk-assessment

This is the implementation of the guide's Step 3.5 design prompt, adapted to the
actual schemas in this repository. It is a planning method, not an assertion that
the council has failed a control. Python resolves figures and computes scores.

## Preconditions and boundaries

Read `outputs/rules.json`, `outputs/analytics.json` and `outputs/history.json` in
full. They must have passed their verifiers and reconciliation checks. Stop if
any is missing/malformed. Do not read original transaction tables or PDFs. Do not
edit inputs, this skill, the builder, the baseline or auditor decisions. You may
confirm a sample CSV exists without reading its rows.

Read `outputs/auditor-comments.md` first if it exists. A blank Decision means no
decision. Only the human auditor approves scope. Never infer a decision from
silence, a recommendation or an earlier illustrative fixture.

## Step 1: Work through these themes

Use actual rule IDs by checking the clause in rules.json; do not transfer an ID
from a guide illustration. Numeric object keys are supported in JSON paths.

| Theme | Actual evidence paths / source clauses | Interpretation and sample source |
|---|---|---|
| Procurement route and aggregation | `$.tests.split_purchases.25000.headline_general_procurement`; `$.tests.threshold_clustering.25000.by_tag`; clauses 6.15–6.16 and App B | Periodic payments need requirement/contract evidence; they do not establish artificial splitting. `split_purchases_windows.csv` / `threshold_clustering_full.csv`. |
| Register and competition evidence | `$.tests.high_value_suppliers.headline_general_procurement`; `$.tests.off_contract`; `$.contracts.register_present`; clauses 5.2.1, 10.4, App B | Only exact names count as matches; near names need confirmation. No notice is not off-contract proof. Distinguish the lower single-quote population from the notice-eligible population. `supplier-match.csv` or `high_value_suppliers_flagged.csv`. |
| Duplicate-payment controls | `$.tests.duplicates.different_time`, `$.tests.duplicates.same_timestamp`; clause 10.7.9.1; AUD-15 | Payment-run timestamps are not invoice dates. Same-run equal amounts are weak indicators; no prior adverse Accounts Payable opinion may be invented. `duplicates.csv`. |
| Contract extensions | `$.tests.expired_notice_spend`; App C row D | Public notices are incomplete; expiry requires a register and extension check. `expired_notice_spend.csv`. |
| Contract variations | `$.tests.spend_vs_award`; App C row E | Annualised run-rate is an estimate; whole-term award values are not actual losses. Multiple active awards cannot be allocated from supplier totals. `spend_vs_award.csv`. |
| Waivers, award authority and records | Clauses 4.2, 7.3–7.5, 9.1–9.3, App A | Public payments cannot establish approvals, waiver compliance or retention. Recommend a document/enquiry test and state the visibility gap. Empty sample_source is appropriate. |
| Individual care/education choice records | App C row F; AUD-16 and AUD-18 with their actual differing opinions; placement tag summaries | The tag is a screening proxy, not proof every row qualifies for an exemption. Competition may be exempt while case-note reasons remain required. Do not treat a different care audit as a repeat finding on this specific control. |
| Grants / other groups | Clause 1.6.2 is a sourced definition in the excluded list; App B and approval rules still apply where relevant | Grants were retained and separately tagged. Do not label a grant a purchase-control breach from its narrative alone. |

A theme with no real rule, metric or history item is excluded with a reason.
Keep a compact set of distinct risks. Do not manufacture a risk merely to cover
every rule: the later planner accounts explicitly for rules not tested.

## Step 2: Likelihood rubric

Apply this ordered rubric to a specifically defined control risk. These are
consistent planning judgments using the council's labels, not empirical
probabilities estimated from payments. Describe uncertainty explicitly.

| Base likelihood | Evidence standard |
|---|---|
| 1 | Current direct control evidence supports effectiveness and there is no contrary eligible indicator. Absence of a public flag alone is insufficient. |
| 2 | Rule/visibility gap only, public-notice absence alone, same-timestamp equal payments alone, or a pattern substantially explained by the published data limitations. |
| 3 | A nonzero eligible general-procurement pattern directly relevant to the stated control, with source metrics and the alternative explanation stated. This is the normal ceiling for an uncorroborated transaction indicator. |
| 4 | Independent current evidence establishes a relevant control weakness and a corroborating eligible indicator. Two correlated transformations of the same payments are not independent evidence. |
| 5 | Reserved for clear current evidence of sustained recurrence; do not infer certainty from one quarter of public payments. |

An adverse prior audit on the **same control/theme** adds one point, capped at
five. Set `repeat_audit_id`, cite it in the likelihood justification and explain
the exact overlap. The builder checks the adverse opinion and computes whether
the proposed score equals base plus one. A Reasonable/Substantial opinion,
advisory review, generic risk theme, or unrelated adverse school audit never
qualifies. A named prior audit is not evidence that specific agreed actions are
open: history records that those action lists are absent.

## Step 3: Impact method and source discrepancies

Use the actual `scoring_method.impact_scale` descriptors in history.json. Cite
the selected entry, e.g. `[history:$.scoring_method.impact_scale[2]]`, and the
rule/metric supporting the consequence scenario. Explain why that level is
plausible. Payment totals and annualised estimates are exposure indicators, not
measured or assumed loss. Never map gross spend automatically into the financial
loss bands. Where no loss estimate exists, use the printed compliance/operational
descriptor as a clearly labelled scenario and acknowledge the evidence limit.
Critical impact needs specific supporting evidence; it is not a default for a
large supplier. Do not invent a council budget or event probability.

Python uses the exact Figure 1 matrix cells and Table 4 bands from history.json.
It discloses Figure 4's separate corporate-register threshold rather than
substituting it for Table 4. Preserve the Medium score typo, High/Medium–High
wording difference, percentage-band overlap and escalation inconsistency. If
`scoring_method.usable` is false, declare the one-to-five fallback and do not
claim the council endorsed its response bands.

## Step 4: Write risk-ratings.json

Use this structure (example is schema guidance, not a real rating):

```json
{
  "generated_at": "YYYY-MM-DD",
  "risks": [{
    "id": "R-01",
    "title": "Qualitative control risk",
    "risk": "What may fail, stated as an indicator requiring investigation.",
    "likelihood": {
      "base_score": 2,
      "score": 2,
      "justification": "Visibility gap and its limitation [rule:CPR-01]."
    },
    "impact": {
      "score": 3,
      "justification": "Explicit consequence scenario [history:RT-02]."
    },
    "evidence": ["{{$.population.rows_after_exclusions}} retained payments [metric:$.population.rows_after_exclusions]."],
    "proposed_focus": "The evidence the audit should inspect.",
    "recommend_in_scope": true,
    "sample_source": ""
  }],
  "excluded": [{"theme": "Theme not rated", "reason": "Evidence-based explanation."}]
}
```

Every likelihood and impact justification needs at least one resolvable
`[rule:CPR-NN]`, `[metric:$.actual.path]` or `[history:ID]` citation. A history path
must identify an actual object with source, pdf_page and quote. All data figures
in prose use scalar `{{$.path}}` placeholders. Never type a data count, amount,
percentage or date into prose. Digits in IDs/citation paths and numeric score
fields are allowed. Supplier names must not appear in titles, risk statements,
justifications or proposed focus. Evidence must not characterise a supplier.
`sample_source` is a filename relative to analytics-full; leave it empty for
document-only tests. Never invent a filename.

For a revision, keep all approved risk objects byte-for-byte equivalent as JSON
values. The human may approve, reject with a reason, or request exact amendments.
The Comment cell for amendments contains JSON field changes, for example
`{"recommend_in_scope": false}`. A natural-language instruction must first be
faithfully transcribed into these exact changes by the lead from the human's
explicit instruction; you may not create or amend decisions yourself. Score
changes must include the corresponding cited justification. An evidence-limited
human score override also sets `auditor_override: true` in the human's requested
changes and quotes the auditor's rationale in the amended justification.

Rejected risks move to excluded with their ID and the exact auditor reason. Add:

```json
"revision": {"number": 1, "changes": [
  {"id": "R-02", "action": "amended"},
  {"id": "R-03", "action": "rejected"}
]}
```

Approvals with no amendments still require a revision with an empty changes
list. The builder compares all objects to its validated baseline and blocks
unrequested changes, unapplied amendments and false revision claims. Partial
decisions leave untouched risks undecided; only the planning gate requires every
risk to have a decision. New risks require explicit auditor instructions and a reviewed baseline;
stop and ask the lead to handle that change rather than altering the baseline.

## Step 5: Build and validate

Run `.venv/bin/python .claude/skills/risk-assessment/build_register.py`.
Fix every FAIL and WARN by correcting ratings, not the inputs or validator. A
broken risk is dropped from the valid set; diagnostics identify it. A build with
any error or warning cannot publish or overwrite the last validated register.
Remove an unsupported risk and explain the exclusion, or supply real evidence.
Never add a tag merely to satisfy the checker without reading its source.

On success the builder writes risk-register.md, the blank/preserved decision
template and the current validated baseline for the next review. Read the rendered register, verify
the summary and disclosures, and check that real decisions were preserved.

## Step 6: Report

Under four hundred words: themes, summary table, cited rationale for priority,
important gaps and exclusions, repeat uplifts, scoring inconsistencies and any
auditor override. Figures must be read from rendered output. End by asking the
human auditor to record a decision for every risk in auditor-comments.md. Never
approve scope or produce the planning pack before that gate is closed.

A successful revision also writes risk-approval-state.json, binding the exact
ratings, decision template, rendered register, baseline and three evidence inputs.
The planning gate and trace QA reject later edits until the register is rebuilt.
This is file-version validation, not a signature or a substitute for human
authorisation. The lead preserves reviewed versions in Git before advancing.
