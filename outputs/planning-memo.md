# Procurement audit: planning memo

*Prepared 2026-10-15. Scope approved by Jay Yu dated 2026-10-15 (register revision 1). See [review and sign-off](review.md).*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

## Purpose

Plan evidence-based fieldwork on the human-approved procurement risks, specifying the controls, records and tests needed to reach supported conclusions. Human sign-off follows independent challenge and QA review.

## Background

The supplied public payment files cover 3 months, from 2026-05-01 to 2026-07-31. After documented exclusions, the analytical population is 8,534 payments totalling £66,778,104.78 [metric:$.population.rows_after_exclusions][metric:$.population.total_gbp].
The source rules, committee evidence and independent analytical checks inform the approved register. Payment patterns identify cases to investigate; they do not establish control failures.

## Scope

The register lists 7 rated risks. The auditor recorded 7 decisions by Jay Yu dated 2026-10-15: 7 risks are approved and in scope, and 0 are not.

| ID | Risk | Score | Band | Decision | Auditor comment |
|---|---|---|---|---|---|
| R-01 | Competitive-quote threshold clustering and anti-splitting indicator in general procurement | 9 | Medium - High | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-02 | Contract register and competitive-process evidence gap for high-value general procurement spend | 6 | Moderate | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-03 | Duplicate-payment indicator in general procurement payment runs | 6 | Moderate | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-04 | Contract extension without visible approval after notice expiry | 6 | Moderate | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-05 | Annualised payment run-rate above the matched award annual rate (variation-control indicator) | 9 | Medium - High | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-06 | Waiver, exception and delegated award-approval documentation visibility gap | 6 | Moderate | approve | Approved for inclusion; no separate grant-only fieldwork |
| R-07 | Case-note record-keeping for exempted individual care and education placement choices | 6 | Moderate | approve | Approved for inclusion; no separate grant-only fieldwork |

## Approach

The human approved every rated risk without amendment and explicitly accepted no separate grant-only fieldwork. Scope approval is recorded in the comments and validated register revision. The pack translates that scope into source-backed controls, pass/fail fieldwork steps and deterministic targeted samples.
Higher-rated risks receive larger targeted selections; duplicate tiers are tested separately. Group samples retain the full payment window. Supplier samples anchor requests to selected payments but require the complete underlying contract and payment history before a conclusion. Reusing a row for a different control does not create independent evidence; reported sample occurrences and amounts must not be read as unique coverage or loss.
Document-only work starts from the complete client-provided population, which is not available in these inputs. Missing records, disputed applicability and unresolved VAT or threshold questions are reported as limitations, not assumed failures. Independent review and deterministic checks support the separate human sign-off decision.

The programme holds 10 expected controls and 11 test steps, with 267 sampled transactions worth £30,535,420.19, each traceable to its row in the council's published workbooks (see `audit-program.md` and `outputs/samples/`).

## Rules coverage

30 of 74 rules in `rules.json` are cited by a risk, a control or a test. The remaining 44 are not tested in this audit, for these reasons:

- Budget authorisation is a separate control outside the approved targeted tests. These public payments do not include the approved budget and commitment records needed to test it; no assurance is claimed.: CPR-01
- Publication of the expenditure feed and monthly procurement-board reporting are outside the approved targeted contract-register and notice tests. Availability of these supplied files is not proof of complete or timely publication/reporting.: CPR-03, CPR-06
- Cross-border advertising and detailed tender receipt, secure opening and late-submission procedures are outside the targeted quotation/notice tests. The source publication duty is retained; tender files and route applicability would be needed for separate fieldwork.: CPR-08, CPR-11, CPR-12, CPR-13, CPR-14
- Award-report retention, agreement-form approval, contract terms and sealed-document custody are separate legal/record controls outside the approved targeted indicators. Actual contracts and retention histories are not available; no conclusion is made about these controls.: CPR-25, CPR-26, CPR-27, CPR-28, CPR-29, CPR-31, CPR-32, CPR-33, CPR-34, CPR-35, CPR-36, CPR-37, CPR-38, CPR-39, CPR-41, CPR-42
- Indemnity, performance security, insurance, construction tax checks, execution/sealing and counsel instructions are outside these targeted tests. They require contract-specific triggers and records absent from public payment and notice inputs.: CPR-43, CPR-44, CPR-45, CPR-46, CPR-47, CPR-48, CPR-49, CPR-50, CPR-51, CPR-52, CPR-53, CPR-54, CPR-55, CPR-56
- The lower-value single-quote requirement is not the three-quotation indicator rated in R-01. This plan does not test a separate lower-tier population and does not claim that competition was required throughout it.: CPR-61
- Full tender procedures are not separately tested in this targeted quotation plan. Contract category, total valuation and the missing statutory parameters must be established from council records; applicability discovered in sampled files is referred to the auditor for additional work.: CPR-64, CPR-65
- Alternative statutory/exclusive-rights and Provider Selection Regime routes are not tested by the defined placement-choice case-note procedure. Those different categories require separate applicability evidence and approvals; they are not assumed to qualify for the sampled exemption.: CPR-67, CPR-68, CPR-69

## Limitations

- Published payments cover only amounts over the source publication floor. Redacted suppliers and identified statutory/inter-authority payments are excluded from supplier screening. Payment-run dates are not invoice dates.
- Supplier totals and annualised payment rates do not establish contract value, procurement category, a continuing run-rate, actual overspend or loss. The statutory parameters remain null; the source VAT conflict and exact-boundary drafting gaps require documentary confirmation before selecting the procurement route.
- Contracts Finder is a screening feed, not the council advertising portal or its contract register. Near names are unconfirmed; missing matches do not prove missing contracts. No actual register was supplied.
- The council scoring documents contain conflicting labels and overlapping financial bands. The register retains these and uses the disclosed response-band method. Committee covering reports omit plan appendices, individual action lists and the exempt corporate risk register.
- Grants remain tagged in the analytical population, but this approved scope contains no separate grant-only fieldwork. Placement tags are proxies: the exemption category must be established before applying the case-note requirement.
- Targeted samples support investigation rather than statistical population estimates. Sample occurrences repeat some payments across different controls and overlapping windows.

## Review and sign-off

The challenger's points and their status are in `challenges.md`; points marked *for the auditor* need a decision at sign-off. The QA reviewer's checks and verdict are in `review.md`, which ends with the sign-off block.
