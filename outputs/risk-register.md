# Procurement audit risk register

*Revision 1, following auditor comments: approved risks unchanged.*

Status: risk assessment and auditor scope decisions; indicators are not findings of non-compliance.

Method: the council's likelihood and impact scales, Figure 1 matrix (risk-management-strategy-2024-27.pdf, PDF p.18) and Table 4 response bands (PDF p.19). Python computes likelihood × impact and looks up both printed labels.

Source discrepancies retained: Table 1 / Figure 1 use Medium impact at three although the introductory prose prints two; Figure 1 calls the middle upper band High while Table 4 calls it Medium–High. Table 4 controls the response band. Figure 4 separately places scores of nine or above on the Corporate Risk Register, while the adjacent prose and Table 4 describe escalation of Extreme risks. That different Figure 4 rule is disclosed, not silently substituted.

The financial percentage bands overlap in the source. No inferred budget, loss estimate or probability is calculated from payment totals. Impact is an explicit consequence scenario using the printed descriptors; likelihood is a consistent planning judgment under the skill rubric, not a measured event probability.

## Summary

| ID | Risk | L | I | Score | Matrix label | Response band | Proposed focus | Scope |
|---|---|---:|---:|---:|---|---|---|---|
| R-01 | Competitive-quote threshold clustering and anti-splitting indicator in general procurement | 3 | 3 | 9 | High | Medium - High | Confirm, from procurement files for the flagged supplier windows, whether each payment reflects a genuinely separate requirement with its own three-quote evidence, or whether a single requirement was disaggregated. | In |
| R-02 | Contract register and competitive-process evidence gap for high-value general procurement spend | 2 | 3 | 6 | Moderate | Moderate | Request the council's actual contract register (not the public notice feed) and reconcile a sample of the unmatched high-value general-procurement suppliers against it before treating any as off-contract. | In |
| R-03 | Duplicate-payment indicator in general procurement payment runs | 3 | 2 | 6 | Moderate | Moderate | Pull the flagged same-amount, same-supplier pairs and confirm against invoices whether each represents one obligation paid once. | In |
| R-04 | Contract extension without visible approval after notice expiry | 2 | 3 | 6 | Moderate | Moderate | Check the council's contract file and extension approval record for each flagged supplier against the rule's approval requirement before treating any as unapproved. | In |
| R-05 | Annualised payment run-rate above the matched award annual rate (variation-control indicator) | 3 | 3 | 9 | High | Medium - High | Reconcile the flagged supplier payments to the matched award's scope and payment schedule, then inspect any relevant variation approvals. Do not treat the annualised ratio as an actual whole-term overspend. | In |
| R-06 | Waiver, exception and delegated award-approval documentation visibility gap | 2 | 3 | 6 | Moderate | Moderate | Request the council's waiver/exception log and delegated-award approval records and test a sample against the named-approver requirements for each value tier. | In |
| R-07 | Case-note record-keeping for exempted individual care and education placement choices | 2 | 3 | 6 | Moderate | Moderate | Sample case notes for payments tagged as care-or-education placements against the Appendix C exemption categories and confirm the reason for choice of provider is recorded. | In |

## R-01: Competitive-quote threshold clustering and anti-splitting indicator in general procurement

A number of general-procurement payments sit near the three-written-quotation threshold, and some of the same suppliers show repeat payment windows whose combined total crosses that same threshold while each individual payment stays under it. This is an indicator to investigate whether the three-quote requirement or the anti-splitting rule may have been tested or circumvented in specific cases; it is not a finding that this occurred, and it is not a claim of statistically excessive clustering across the population. Periodic, genuinely separate requirements to the same supplier are not splitting.

Likelihood (3): A nonzero eligible general-procurement pattern directly relevant to the three-written-quotation threshold and the anti-splitting rule, with the comparator and the alternative explanation both stated [rule:CPR-62][rule:CPR-63][rule:CPR-10]: using the test's own near-threshold band (from 0.90 of the threshold up to the threshold itself, benchmarked against a wider 0.50-to-1.50 baseline), 10 general-procurement payments fall in that band [metric:$.tests.threshold_clustering.25000.by_tag[1].rows], and 46 general-procurement supplier windows show repeat payments within the test's window crossing the same threshold [metric:$.tests.split_purchases.25000.by_tag.general_procurement.windows]. This is an indicator to investigate specific cases, not evidence of population-wide avoidance; genuinely separate, periodic requirements to the same supplier are not splitting, so the score is held at the rubric's normal ceiling for an uncorroborated transaction indicator.

Impact (3): The council's own risk themes name procurement contract and relationship management and value-for-money exposure as a direct consequence of this control area [history:RT-05]. Using the printed Medium compliance/financial descriptor as a plausible, clearly labelled scenario rather than a measured loss [history:$.scoring_method.impact_scale[2]], since avoided or untested competition raises a reasonable possibility of challenge to value for money, not a quantified loss.

Evidence:
- 10 general-procurement payments in the near-threshold band used by the test, totalling 239,427.82 GBP [metric:$.tests.threshold_clustering.25000.by_tag[1].gbp].
- 46 general-procurement supplier windows with combined totals crossing the same threshold, totalling 2,450,650.54 GBP [metric:$.tests.split_purchases.25000.by_tag.general_procurement.gbp].
- The three-written-quotation threshold rule and the no-splitting rule both apply to this condition [rule:CPR-62][rule:CPR-10].

Proposed focus: Confirm, from procurement files for the flagged supplier windows, whether each payment reflects a genuinely separate requirement with its own three-quote evidence, or whether a single requirement was disaggregated.
Sample source: `split_purchases_windows.csv`

## R-02: Contract register and competitive-process evidence gap for high-value general procurement spend

Three distinct things sit behind this risk and must not be conflated: (a) the rule requiring publication of invitation-to-tender/quote details above a value threshold; (b) the separate rule requiring a contract notice to be published on the council's own advertising portal (CDP) once a goods/services or works contract reaches the three-written-quotation tier; and (c) Contracts Finder, the external public notice export used here purely as a screening tool for whether a CDP-type notice can be found, which is not itself the council's contract register. The council's own register of contracts in progress and awarded, required separately by the rules, was not present among the inputs reviewed; that absence is a statement about this review's inputs, not a conclusion about whether the council maintains such a register elsewhere. Separately, a material share of high-value general-procurement spend above the Contracts Finder publication threshold has no matching notice in that external export. Absence of a Contracts Finder match is not proof the underlying CDP notice or the register entry is missing, since Contracts Finder has its own publication gaps.

Likelihood (2): This is a rule and visibility gap: the required contract register was not present among the inputs reviewed [rule:CPR-05][metric:$.contracts.register_present], which does not establish that the council has no such register, only that this review could not inspect one; and public-notice absence in the external Contracts Finder screening data alone is the weaker evidence standard in the rubric. 190 eligible general-procurement suppliers above the publication threshold have no exact Contracts Finder match [metric:$.tests.off_contract.unmatched_by_tag[2].count], but the test's own caveat is that this is a screening indicator to check against the council's own CDP notices and register, never proof of off-contract spend.

Impact (3): Contracts and partnerships risk, including procurement contract management, is a named council risk category [history:RT-05]. The printed Medium compliance descriptor is used as the plausible consequence scenario for an unverifiable register and competition trail, given a reasonable possibility of regulatory or audit interest rather than a measured loss [history:$.scoring_method.impact_scale[2]].

Evidence:
- The council's own contracts register was not present among the inputs reviewed [metric:$.contracts.register_present].
- 190 eligible general-procurement suppliers above the publication threshold of 25,000 GBP show no exact Contracts Finder match, totalling an annualised 99,520,666.56 GBP [metric:$.tests.off_contract.unmatched_by_tag[2].gbp_annualised].
- The invitation-to-tender publication duty, the CDP contract-notice duty and the contract-register duty are each separate requirements that apply to this spend [rule:CPR-04][rule:CPR-62][rule:CPR-05].

Proposed focus: Request the council's actual contract register (not the public notice feed) and reconcile a sample of the unmatched high-value general-procurement suppliers against it before treating any as off-contract.
Sample source: `supplier-match.csv`

## R-03: Duplicate-payment indicator in general procurement payment runs

A number of general-procurement payments to the same supplier for the same amount recur within a short window, which could indicate a duplicate payment, but payment-run timestamps are not invoice dates and one genuine invoice can be split across a run or batch. This is a weak, screening-level indicator only.

Likelihood (3): Two nonzero eligible general-procurement patterns directly relevant to the payment-obligation control each support this score in their own right, not merely as corroboration of one another [rule:CPR-40]: 33 same-timestamp general-procurement duplicate groups [metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.groups] and, independently, 39 different-time general-procurement duplicate groups within the test's own short window [metric:$.tests.duplicates.different_time.by_tag.general_procurement.groups]. The payment-run timestamp is not an invoice date, so one genuine invoice can be split across a run or batch; this alternative explanation is preserved. No repeat-finding uplift applies: the most relevant completed control audit, Accounts Payable, found Reasonable Assurance with no adverse opinion on this payment process, which is additional context rather than a repeat finding [history:AUD-15].

Impact (2): The printed Minor compliance/financial descriptor is used as the consequence scenario: a low possibility of legal challenge or regulatory interest for a screening-level payment indicator, not a measured loss [history:$.scoring_method.impact_scale[1]]. This is also consistent with compliance being a named impact-rating criterion for contract-related exposure generally [history:RT-02].

Evidence:
- 72 general-procurement rows in same-timestamp duplicate groups, 60,213.42 GBP beyond the first instance [metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.gbp_beyond_first].
- 86 general-procurement rows in different-time duplicate groups, 299,374.24 GBP beyond the first instance [metric:$.tests.duplicates.different_time.by_tag.general_procurement.gbp_beyond_first].
- Payment obligations under the contract rules apply to these transactions [rule:CPR-40].

Proposed focus: Pull the flagged same-amount, same-supplier pairs and confirm against invoices whether each represents one obligation paid once.
Sample source: `duplicates.csv`

## R-04: Contract extension without visible approval after notice expiry

A small number of suppliers continued to be paid after every matching Contracts Finder notice had ended, which may indicate an extension was exercised without the required approval. A newer contract or notice may simply not appear in this published data, so this is an indicator to check against the register, not evidence of an unapproved extension.

Likelihood (2): This is a rule and visibility gap substantially explained by the published data's limitations [rule:CPR-70]: 7 suppliers were paid after every matching notice ended, totalling an annualised 761,467.68 GBP [metric:$.tests.expired_notice_spend.count], but the test's own note is that a newer contract may exist with no notice published.

Impact (3): Contracts and partnerships risk, including dependency on contractors continuing to deliver without a confirmed current agreement, is a named council risk category [history:RT-05]. The printed Medium compliance descriptor is used as the plausible scenario, given a reasonable possibility of regulatory or audit interest in an apparently lapsed agreement [history:$.scoring_method.impact_scale[2]].

Evidence:
- 7 suppliers paid after every matching notice had ended, totalling an annualised 761,467.68 GBP [metric:$.tests.expired_notice_spend.gbp_annualised].
- Contract extension under an existing extension provision requires the named finance officer's approval [rule:CPR-70].

Proposed focus: Check the council's contract file and extension approval record for each flagged supplier against the rule's approval requirement before treating any as unapproved.
Sample source: `expired_notice_spend.csv`

## R-05: Annualised payment run-rate above the matched award annual rate (variation-control indicator)

Annualised payments to suppliers matched to a single active, single-supplier award exceed the award's estimated annual rate (whole-term award value divided by contract years) by the screening ratio used in the test. This may warrant checking variations and the scope attributable to that award. Annualising three months of payments assumes the observed rate continues; supplier payments may cover other requirements, and award values may be estimates or maxima. The ratio does not establish that the whole-term award value has been exceeded or that an unapproved variation occurred.

Likelihood (3): A nonzero eligible pattern directly relevant to the variation-approval control, with the alternative explanation stated [rule:CPR-71][rule:CPR-72]: 8 suppliers exceed the award-value ratio of 1.25 used as the screening indicator [metric:$.tests.spend_vs_award.count], while the test's own caveat is that award values may be estimates or maxima, keeping this at the rubric's normal ceiling for an uncorroborated transaction indicator.

Impact (3): Compliance exposure tied to contract terms, and dependency on contractors delivering within the agreed cost, are named council risk criteria [history:RT-02][history:RT-05]. The printed Medium compliance descriptor is used as the plausible consequence scenario for an unconfirmed variation, not a measured loss [history:$.scoring_method.impact_scale[2]].

Evidence:
- 8 suppliers show annualised payment run-rates at or above 1.25 times the matched award's estimated annual rate [metric:$.tests.spend_vs_award.count][metric:$.tests.spend_vs_award.parameters.indicator_ratio].
- Below the applicable statutory threshold, variation requires written approval by the Monitoring Officer and designated finance officer; above it, the relevant board must consider the specified report and recommendation. The applicable threshold remains a required fieldwork input [rule:CPR-71][rule:CPR-72].

Proposed focus: Reconcile the flagged supplier payments to the matched award's scope and payment schedule, then inspect any relevant variation approvals. Do not treat the annualised ratio as an actual whole-term overspend.
Sample source: `spend_vs_award.csv`

## R-06: Waiver, exception and delegated award-approval documentation visibility gap

The rules set specific named approvers and documentation requirements for waivers, exceptions from competition, and delegated contract-award authority at each value tier. None of this is observable in the published payment data, so compliance can only be tested against the council's own waiver and approval records, not inferred from payment totals.

Likelihood (2): This is the rubric's rule-and-visibility-gap case: the waiver, exception and delegated-authority approval requirements are mandatory controls with no observable metric in the spend population [rule:CPR-18][rule:CPR-22]. Absence of a public flag for a breach is not evidence that approvals were obtained or withheld; only a document test can establish the actual position.

Impact (3): Compliance (litigation, regulatory, contract) is an explicit impact-rating criterion covering this exact control category [history:RT-02]. The printed Medium compliance descriptor is used as the plausible scenario for undocumented or unapproved waivers, given a reasonable possibility of challenge, rather than an assumed loss [history:$.scoring_method.impact_scale[2]].

Evidence:
- No metric in the published spend or notice data can evidence waiver, exception or delegated-award approval; this control requires a document/enquiry test [rule:CPR-18].
- The documentation and recording duty applies to every waiver or exception [rule:CPR-22].

Proposed focus: Request the council's waiver/exception log and delegated-award approval records and test a sample against the named-approver requirements for each value tier.
Sample source: document/enquiry test; no transaction sample assumed.

## R-07: Case-note record-keeping for exempted individual care and education placement choices

Appendix C requires a recorded reason for the choice of provider, in the individual's case notes, for a defined set of social-care and education placement exemptions. This record cannot be seen in payment data at all; the care-or-education placement tag is a screening proxy for the scale of spend potentially subject to the requirement, not evidence that any particular payment lacks the record.

Likelihood (2): This is a visibility-gap case: the case-note requirement has no observable metric in payment data [rule:CPR-73], while the tagged care-or-education placement population is substantial in scale [metric:$.population.tags.care_or_education_placement.rows]. Two completed audits touch adjacent but distinct controls in this area with differing opinions, neither of which extends to this specific case-note requirement, so no repeat uplift is applied [history:AUD-16][history:AUD-18].

Impact (3): Social-care and education placement decisions attract external regulatory and inspection interest, matching the printed Medium descriptor's reputation example of external-agency criticism, used here as the plausible scenario rather than a measured loss [history:$.scoring_method.impact_scale[2]].

Evidence:
- 5,839 payments across the population carry the care-or-education placement tag, totalling 30,571,711.30 GBP, the population within which this exemption category sits [metric:$.population.tags.care_or_education_placement.gbp].
- The case-note record requirement applies to the defined exemption categories [rule:CPR-73].

Proposed focus: Sample case notes for payments tagged as care-or-education placements against the Appendix C exemption categories and confirm the reason for choice of provider is recorded.
Sample source: document/enquiry test; no transaction sample assumed.

## Excluded themes

- Grants and other tagged groups: Grants remain in the retained payment population, tagged analytics and applicable rules. No separate grant-specific fieldwork risk is proposed from these inputs. The general-procurement tests proposed under R-01 and R-02 do not cover grant-only transactions; this is an explicit scope limitation for the auditor to accept or amend, not a conclusion that grant compliance has been tested.

## Source references

- [history:$.scoring_method.impact_scale[1]] risk-management-strategy-2024-27.pdf, PDF p.14: “0.01% 0.1% of annual WBC budget £17.5k £175k”
- [history:$.scoring_method.impact_scale[2]] risk-management-strategy-2024-27.pdf, PDF p.14: “0.1% - 0.3% annual WBC budget £175k -500k”
- [history:AUD-15] audit-completed-work-2025-26-q3.pdf, PDF p.1: “Accounts Payable Reasonable Assurance”
- [history:AUD-16] audit-completed-work-2025-26-q3.pdf, PDF p.1: “Personal Budgets (Direct Payments) Limited Assurance”
- [history:AUD-18] audit-completed-work-2025-26-q3.pdf, PDF p.1: “Purchase of Residential and Nursing Care Provision Reasonable Assurance”
- [history:RT-02] risk-management-strategy-2024-27.pdf, PDF p.14: “Compliance (litigation, regulatory, contract)”
- [history:RT-05] risk-management-strategy-2024-27.pdf, PDF p.33: “Dependency on, or failure of, contractors to deliver services or products to the agreed cost and specification. Procurement contract and relationship management.”
- [metric:$.contracts.register_present] analytics.json: false
- [metric:$.population.tags.care_or_education_placement.gbp] analytics.json: 30,571,711.30
- [metric:$.population.tags.care_or_education_placement.rows] analytics.json: 5,839
- [metric:$.tests.duplicates.different_time.by_tag.general_procurement.gbp_beyond_first] analytics.json: 299,374.24
- [metric:$.tests.duplicates.different_time.by_tag.general_procurement.groups] analytics.json: 39
- [metric:$.tests.duplicates.different_time.by_tag.general_procurement.rows] analytics.json: 86
- [metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.gbp_beyond_first] analytics.json: 60,213.42
- [metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.groups] analytics.json: 33
- [metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.rows] analytics.json: 72
- [metric:$.tests.expired_notice_spend.count] analytics.json: 7
- [metric:$.tests.expired_notice_spend.gbp_annualised] analytics.json: 761,467.68
- [metric:$.tests.off_contract.parameters.publication_threshold] analytics.json: 25,000
- [metric:$.tests.off_contract.unmatched_by_tag[2].count] analytics.json: 190
- [metric:$.tests.off_contract.unmatched_by_tag[2].gbp_annualised] analytics.json: 99,520,666.56
- [metric:$.tests.spend_vs_award.count] analytics.json: 8
- [metric:$.tests.spend_vs_award.parameters.indicator_ratio] analytics.json: 1.25
- [metric:$.tests.split_purchases.25000.by_tag.general_procurement.gbp] analytics.json: 2,450,650.54
- [metric:$.tests.split_purchases.25000.by_tag.general_procurement.windows] analytics.json: 46
- [metric:$.tests.threshold_clustering.25000.by_tag[1].gbp] analytics.json: 239,427.82
- [metric:$.tests.threshold_clustering.25000.by_tag[1].rows] analytics.json: 10
- [metric:$.tests.threshold_clustering.25000.parameters.baseline_lower_fraction] analytics.json: 0.50
- [metric:$.tests.threshold_clustering.25000.parameters.baseline_upper_fraction] analytics.json: 1.50
- [metric:$.tests.threshold_clustering.25000.parameters.lower_band_fraction] analytics.json: 0.90
- [rule:CPR-04] clause 5.2, PDF p.3: “Details of every invitation to tender for contracts to provide goods and/or services with a value that exceeds £5,000.”
- [rule:CPR-05] clause 5.2.1, PDF p.3: “A register of contracts, including those in progress and those awarded, with key information such as the contract value, duration and supplier.”
- [rule:CPR-10] clause 6.16, PDF p.5: “There shall be no artificial splitting or disaggregation of a contract to avoid the application of the provisions of the Procurement Legislation and/or these Rules.”
- [rule:CPR-18] clause 7.3, PDF p.6: “Only the Monitoring Officer and/or the S.151 Officer may grant a waiver or an exception to these Rules, subject to exception values and delegation thresholds detailed in these Rules and/or elsewhere in the Constitution. An officer who seeks a waiver of these Rules shall do so only in advance and only in exceptional circumstances.”
- [rule:CPR-22] clause 7.5.1, PDF p.6: “All exceptions or waivers to these Rules must: 7.5.1 be fully documented;”
- [rule:CPR-40] clause 10.7.9.1, PDF p.8: “any payment due from the Council is made no later than 30 days from the date on which the relevant invoice is regarded as valid and undisputed; and”
- [rule:CPR-62] clause App B row B1, PDF p.12: “Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including at least one SME* or VCSE* organisation and one local supplier ****(where appropriate and possible**).”
- [rule:CPR-63] clause App B row B2, PDF p.12: “Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including at least one SME* or VCSE* organisation and one local supplier **** (where appropriate and possible**).”
- [rule:CPR-70] clause App C row D, PDF p.14: “Approval of the S151 Officer”
- [rule:CPR-71] clause App C row E (below Threshold), PDF p.14: “For contract value below the Threshold prior written approval from the Monitoring Officer and S151 Officer is required.”
- [rule:CPR-72] clause App C row E (above Threshold), PDF p.14: “For contract value greater than the Threshold, approval of the relevant board, following the submission of an extension report to the relevant board with recommendation from Monitoring Officer and S151 Officer”
- [rule:CPR-73] clause App C row F, PDF p.15: “Service Directors must ensure that a record of the reasons for the choice of provider is maintained on the individual’s case notes.”

## Auditor decisions

- R-01: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-02: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-03: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-04: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-05: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-06: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
- R-07: approve; Approved for inclusion; no separate grant-only fieldwork. Applied in this revision.
