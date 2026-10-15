# Audit program

*Prepared 2026-10-15. Scope approved by Jay Yu dated 2026-10-15 (register revision 1). See [review and sign-off](review.md).*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

7 risks in scope, 10 controls, 11 tests, 267 sampled transactions. Samples are drawn by the builder from `analytics-full/` by the recipe stated under each test, and every transaction is listed with its workbook row.


## R-01: Competitive-quote threshold clustering and anti-splitting indicator in general procurement [9 (High; Medium - High)]

**Audit objective.** Determine whether sampled requirements were valued and aggregated appropriately and routed through the applicable quotation process.

**C-01.1. Expected control.** Contracts are not artificially split or disaggregated to avoid procurement requirements. [CPR-10] Owner: Not specified in the cited clauses; confirm the operational owner with the council..

**T-01.1. Test.** For every selected window obtain the orders, specifications, quotes, budgets and related commitments before and after the window. Establish the genuine requirement, whole-life value, category and relevant VAT basis. Compare dates, deliverables and authorisations to decide whether purchases were separate requirements or one requirement disaggregated. A pass requires documentary support for the aggregation and route; a repeated supplier or a combined payment total alone is not a failure. Escalate ambiguous rule boundaries without guessing a statutory value. [CPR-10, CPR-62, CPR-63, metric:$.tests.split_purchases.25000.headline_general_procurement.windows]  
**Evidence to inspect:** Requisitions, purchase orders, specifications, contemporaneous valuation and aggregation rationale, quotation files and approvals.  
**Sample:** 10 items from `split_purchases_windows.csv`, where dominant_tag = general_procurement, threshold_value = 25000, largest window_total first; 180 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2181` | 2026-05-05 | VolkerHighways Ltd | £9,068.36 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2178` | 2026-05-05 | VolkerHighways Ltd | £16,916.01 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:695` | 2026-05-05 | VolkerHighways Ltd | £15,041.26 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2177` | 2026-05-05 | VolkerHighways Ltd | £16,876.43 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2174` | 2026-05-05 | VolkerHighways Ltd | £4,764.64 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:723` | 2026-05-05 | VolkerHighways Ltd | £18,033.36 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:713` | 2026-05-05 | VolkerHighways Ltd | £7,742.55 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:727` | 2026-05-11 | VolkerHighways Ltd | £3,196.62 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:714` | 2026-05-12 | VolkerHighways Ltd | £1,550.00 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:724` | 2026-05-12 | VolkerHighways Ltd | £7,828.20 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:701` | 2026-05-12 | VolkerHighways Ltd | £17,896.87 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:696` | 2026-05-12 | VolkerHighways Ltd | £2,566.36 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:703` | 2026-05-13 | VolkerHighways Ltd | £12,297.34 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2179` | 2026-05-19 | VolkerHighways Ltd | £17,882.35 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2193` | 2026-05-19 | VolkerHighways Ltd | £1,668.58 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:731` | 2026-05-20 | VolkerHighways Ltd | £2,585.44 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2185` | 2026-05-20 | VolkerHighways Ltd | £19,420.72 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:728` | 2026-05-20 | VolkerHighways Ltd | £10,169.81 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2170` | 2026-05-20 | VolkerHighways Ltd | £16,304.62 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2172` | 2026-05-22 | VolkerHighways Ltd | £2,070.26 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:730` | 2026-05-22 | VolkerHighways Ltd | £1,679.16 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:734` | 2026-05-22 | VolkerHighways Ltd | £5,199.81 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2182` | 2026-05-26 | VolkerHighways Ltd | £4,046.54 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:726` | 2026-05-26 | VolkerHighways Ltd | £2,610.11 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:697` | 2026-05-26 | VolkerHighways Ltd | £1,711.48 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2180` | 2026-05-26 | VolkerHighways Ltd | £7,015.34 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:721` | 2026-05-26 | VolkerHighways Ltd | £10,122.39 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:716` | 2026-05-26 | VolkerHighways Ltd | £850.00 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:715` | 2026-05-26 | VolkerHighways Ltd | £5,225.72 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:693` | 2026-05-27 | VolkerHighways Ltd | £5,997.50 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:699` | 2026-05-27 | VolkerHighways Ltd | £1,793.45 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:694` | 2026-05-27 | VolkerHighways Ltd | £8,175.00 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:9` | 2026-05-28 | The Better Group Ltd | £20,457.43 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:10` | 2026-05-28 | The Better Group Ltd | £19,605.14 | Children's Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:11` | 2026-05-28 | The Better Group Ltd | £2,557.08 | Education & SEND |
| 2 | `Over500_2026_P03_-_published.xlsx:13` | 2026-06-01 | The Better Group Ltd | £24,088.98 | Children's Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2397` | 2026-06-01 | The Better Group Ltd | £22,361.26 | Adult Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:16` | 2026-06-01 | The Better Group Ltd | £15,478.22 | Children's Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:19` | 2026-06-01 | The Better Group Ltd | £3,142.04 | Education & SEND |
| 2 | `Over500_2026_P03_-_published.xlsx:20` | 2026-06-01 | The Better Group Ltd | £2,018.90 | Education & SEND |
| 2 | `Over500_2026_P03_-_published.xlsx:26` | 2026-06-01 | The Better Group Ltd | £16,151.18 | Adult Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2396` | 2026-06-01 | The Better Group Ltd | £18,039.18 | Adult Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:379` | 2026-06-09 | The Better Group Ltd | £14,706.64 | Adult Social Care - Transformation Projects |
| 2 | `Over500_2026_P03_-_published.xlsx:394` | 2026-06-09 | The Better Group Ltd | £12,427.19 | Adult Social Care - Transformation Projects |
| 2 | `Over500_2026_P03_-_published.xlsx:395` | 2026-06-09 | The Better Group Ltd | £11,180.63 | Adult Social Care - Transformation Projects |
| 2 | `Over500_2026_P03_-_published.xlsx:27` | 2026-06-25 | The Better Group Ltd | £2,557.48 | Children's Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:15` | 2026-06-25 | The Better Group Ltd | £2,668.67 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:357` | 2026-06-01 | Newbury & District Ltd | £6,349.35 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:268` | 2026-06-01 | Newbury & District Ltd | £13,826.61 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:171` | 2026-06-02 | Newbury & District Ltd | £10,529.33 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:341` | 2026-06-02 | Newbury & District Ltd | £794.67 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:336` | 2026-06-02 | Newbury & District Ltd | £9,861.00 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:264` | 2026-06-12 | Newbury & District Ltd | £6,331.70 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:269` | 2026-06-12 | Newbury & District Ltd | £14,852.00 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:360` | 2026-06-30 | Newbury & District Ltd | £4,465.96 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:359` | 2026-06-30 | Newbury & District Ltd | £5,921.50 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:274` | 2026-06-30 | Newbury & District Ltd | £13,663.85 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:251` | 2026-06-30 | Newbury & District Ltd | £627.37 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:213` | 2026-06-30 | Newbury & District Ltd | £8,312.63 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:176` | 2026-06-30 | Newbury & District Ltd | £7,785.00 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:302` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £7,911.27 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:301` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £1,039.14 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:300` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £999.32 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:253` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £2,118.96 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:450` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,615.23 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:451` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £574.66 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:246` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £4,549.40 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:309` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £2,974.60 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:452` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,483.38 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:196` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £862.12 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:195` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £730.27 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:459` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £2,312.52 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:183` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £8,226.54 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:181` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £1,197.90 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:245` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £1,214.56 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:311` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £1,947.39 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:456` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £8,097.04 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:192` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £6,662.12 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:305` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £7,986.00 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:250` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £3,831.07 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:249` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £6,927.61 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:198` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £2,504.93 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:197` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £614.96 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:310` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £1,784.39 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:460` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £726.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:344` | 2026-05-06 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,744.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:345` | 2026-05-06 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,548.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:346` | 2026-05-06 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,500.80 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:347` | 2026-05-06 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,041.67 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:383` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,210.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:265` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,912.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:385` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,324.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:384` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,156.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:382` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,596.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:381` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,716.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:380` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,448.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:390` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,079.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:389` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,744.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:388` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,576.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:387` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,590.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:241` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,288.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:290` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,288.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:289` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,980.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:266` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,092.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:242` | 2026-05-13 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £693.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:430` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,187.50 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:429` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,608.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:428` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,745.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:427` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,925.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:426` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,227.50 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:425` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,550.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:423` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,622.86 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:294` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,244.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:422` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,910.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:251` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £742.50 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:283` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,340.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:284` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £3,120.00 | Education & SEND |
| 5 | `Over500_2026_P02_-_published.xlsx:424` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,940.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:333` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,380.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:346` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,310.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:255` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,710.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:184` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,490.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:228` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,775.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:164` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £1,380.00 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:229` | 2026-06-05 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,760.00 | Education & SEND |
| 6 | `Over500_2026_P04_-_published.xlsx:598` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:601` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:733` | 2026-07-13 | Roadside Technologies Ltd | £11,188.22 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:734` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:735` | 2026-07-13 | Roadside Technologies Ltd | £21,000.00 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:740` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:789` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:1287` | 2026-07-13 | Roadside Technologies Ltd | £10,298.22 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:1288` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:597` | 2026-07-30 | Roadside Technologies Ltd | £1,000.00 | Environment |
| 7 | `Over500_2026_P02_-_published.xlsx:530` | 2026-05-27 | Elior UK PLC | £23,694.03 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:434` | 2026-06-11 | Elior UK PLC | £11,935.93 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:440` | 2026-06-16 | Elior UK PLC | £23,516.69 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:433` | 2026-06-17 | Elior UK PLC | £18,592.30 | Adult Social Care |
| 8 | `Over500_2026_P02_-_published.xlsx:240` | 2026-05-12 | BROADWAY CARS | £1,213.33 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:372` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:371` | 2026-05-12 | BROADWAY CARS | £2,240.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:369` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:368` | 2026-05-12 | BROADWAY CARS | £2,100.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:364` | 2026-05-12 | BROADWAY CARS | £3,747.69 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:367` | 2026-05-12 | BROADWAY CARS | £2,800.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:288` | 2026-05-12 | BROADWAY CARS | £2,426.67 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:314` | 2026-05-13 | BROADWAY CARS | £595.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:245` | 2026-05-13 | BROADWAY CARS | £2,076.67 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:391` | 2026-05-13 | BROADWAY CARS | £1,785.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:394` | 2026-05-13 | BROADWAY CARS | £3,220.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:395` | 2026-05-13 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:396` | 2026-05-13 | BROADWAY CARS | £3,010.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:297` | 2026-05-13 | BROADWAY CARS | £1,148.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:404` | 2026-05-26 | BROADWAY CARS | £4,015.38 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:403` | 2026-05-26 | BROADWAY CARS | £3,000.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:415` | 2026-05-27 | BROADWAY CARS | £1,785.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:414` | 2026-05-27 | BROADWAY CARS | £3,220.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:416` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:418` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:419` | 2026-05-27 | BROADWAY CARS | £3,010.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:412` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:410` | 2026-05-27 | BROADWAY CARS | £2,400.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:326` | 2026-05-27 | BROADWAY CARS | £595.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:299` | 2026-05-27 | BROADWAY CARS | £1,230.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:292` | 2026-05-27 | BROADWAY CARS | £2,600.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:250` | 2026-05-27 | BROADWAY CARS | £2,225.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:249` | 2026-05-27 | BROADWAY CARS | £1,300.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:411` | 2026-05-27 | BROADWAY CARS | £2,250.00 | Education & SEND |
| 9 | `Over500_2026_P03_-_published.xlsx:688` | 2026-06-01 | R&A Haines Building Contractors | £20,332.89 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:733` | 2026-06-01 | R&A Haines Building Contractors | £9,666.85 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:709` | 2026-06-09 | R&A Haines Building Contractors | £5,487.25 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:740` | 2026-06-30 | R&A Haines Building Contractors | £16,600.00 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:742` | 2026-06-30 | R&A Haines Building Contractors | £18,707.55 | Development & Housing |
| 9 | `Over500_2026_P04_-_published.xlsx:628` | 2026-07-01 | R&A Haines Building Contractors | £666.28 | Development & Housing |
| 10 | `Over500_2026_P03_-_published.xlsx:641` | 2026-06-17 | Triple Value Impact | £13,275.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:642` | 2026-06-17 | Triple Value Impact | £6,612.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:2392` | 2026-06-17 | Triple Value Impact | £10,787.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:2393` | 2026-06-17 | Triple Value Impact | £13,110.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:649` | 2026-06-18 | Triple Value Impact | £24,244.00 | Chief Executive |

**C-01.2. Expected control.** Applicable quotation invitations use the portal and appropriate sources, with evaluation criteria communicated in advance, best-value award decisions and no prohibited supplier preference. [CPR-15, CPR-16, CPR-62, CPR-63, CPR-66] Owner: Relevant Service Director approves any best-value award exception in advance; confirm the operational owner for quotation invitations and evaluation with the council..

**T-01.2. Test.** For each selected near-boundary payment, first establish the associated total contract value and category. Where the cited three-quotation tier applies, inspect portal invitations to the required appropriate sources, explanations for any SME/VCSE or local-source practicality exception, pre-notified evaluation criteria, impartial evaluation and best-value award decision. For any claimed exceptional award, inspect the exceptional-circumstances justification and dated relevant Service Director approval obtained before the award. A pass requires the applicable invitations and evaluation trail and either a supported best-value decision or that source-permitted prior-approved exception, with no prohibited preference. Do not demand three responses where the rule requires invitations, or apply this tier solely from a payment amount. [CPR-15, CPR-16, CPR-62, CPR-63, CPR-66, metric:$.tests.threshold_clustering.25000.by_tag[1].rows]  
**Evidence to inspect:** Contract valuation, portal invitations and dates, source-selection rationale, evaluation criteria, scoring and award approval. For an exceptional award, written justification and dated prior Service Director approval.  
**Sample:** 10 items from `threshold_clustering_full.csv`, where tag = general_procurement, threshold_value = 25000, largest Net amount first; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:1281` | 2026-07-29 | The Better Group Ltd | £24,476.02 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:2201` | 2026-05-15 | WOKINGHAM BOROUGH COUNCIL | £24,416.73 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:649` | 2026-06-18 | Triple Value Impact | £24,244.00 | Chief Executive |
| 4 | `Over500_2026_P02_-_published.xlsx:560` | 2026-05-12 | DevComms South East Ltd | £24,227.07 | Development & Housing |
| 5 | `Over500_2026_P03_-_published.xlsx:13` | 2026-06-01 | The Better Group Ltd | £24,088.98 | Children's Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:396` | 2026-06-10 | BookingLab Limited | £24,000.00 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P02_-_published.xlsx:530` | 2026-05-27 | Elior UK PLC | £23,694.03 | Adult Social Care |
| 8 | `Over500_2026_P03_-_published.xlsx:683` | 2026-06-08 | VolkerHighways Ltd | £23,591.22 | Environment |
| 9 | `Over500_2026_P03_-_published.xlsx:440` | 2026-06-16 | Elior UK PLC | £23,516.69 | Adult Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:533` | 2026-07-28 | Elior UK PLC | £23,173.08 | Adult Social Care |


## R-02: Contract register and competitive-process evidence gap for high-value general procurement spend [6 (Moderate; Moderate)]

**Audit objective.** Establish whether the sampled high-value procurement has a traceable contract-register entry and the applicable publication and competition evidence.

**C-02.1. Expected control.** A published register records contracts in progress and awarded, including value, duration and supplier; award notification enables registration. [CPR-05, CPR-30] Owner: Service Lead for Commissioning and Procurement receives award notifications; confirm responsibility for publication from council records..

**T-02.1. Test.** Obtain the published register, its publication location and relevant historic versions. Reconcile each selected supplier payment to the actual legal supplier, contract or lawful route, award notification and register entry. Check recorded value, duration and supplier against the agreement. Record timing gaps and request explanations. A pass requires the actual applicable entry and publication evidence; a Contracts Finder non-match cannot establish failure. [CPR-05, CPR-30, metric:$.contracts.register_present, metric:$.tests.off_contract.unmatched_by_tag[2].count]  
**Evidence to inspect:** Published and internal register versions, award notifications, signed agreements and payment-to-contract reconciliation.  
**Sample:** 5 items from `supplier-match.csv`, where dominant_tag = general_procurement, eligible_for_notice_test = True, match_class = ['none', 'near_contain', 'near_ratio'], largest annualised_estimate first, 2 payments per supplier; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:793` | 2026-07-13 | VolkerHighways Ltd | £998,987.64 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:603` | 2026-07-28 | VolkerHighways Ltd | £855,750.25 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2146` | 2026-06-29 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,180,425.32 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:2216` | 2026-06-03 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:665` | 2026-05-15 | The Better Group Ltd | £64,500.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:666` | 2026-05-15 | The Better Group Ltd | £58,833.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |

**C-02.2. Expected control.** Applicable invitation and contract notices are published through the required channels; CDP publication precedes other advertising and is approved and issued by the specified officer. [CPR-04, CPR-07, CPR-09, CPR-62, CPR-63] Owner: Service Lead for Procurement and Commissioning or delegate for CDP notice approval and issue..

**T-02.2. Test.** For the same selected suppliers establish the contract value, category and applicable route before assessing publication. Inspect invitation details, portal and CDP notices with publication timestamps, and the named officer approval. Compare the distinct invitation-publication and contract-notice duties. A pass requires the evidence applicable to that contract; missing external feed matches alone are inconclusive. If a different statutory tender route applies, obtain the sourced parameters and refer the extra work to the auditor. [CPR-04, CPR-07, CPR-09, CPR-62, CPR-63, metric:$.tests.off_contract.unmatched_by_tag[2].count]  
**Evidence to inspect:** Actual CDP and council portal records, approval trail, timestamps and documented valuation and route.  
**Sample:** 5 items from `supplier-match.csv`, where dominant_tag = general_procurement, eligible_for_notice_test = True, match_class = ['none', 'near_contain', 'near_ratio'], largest annualised_estimate first, 2 payments per supplier; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:793` | 2026-07-13 | VolkerHighways Ltd | £998,987.64 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:603` | 2026-07-28 | VolkerHighways Ltd | £855,750.25 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2146` | 2026-06-29 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,180,425.32 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:2216` | 2026-06-03 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:665` | 2026-05-15 | The Better Group Ltd | £64,500.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:666` | 2026-05-15 | The Better Group Ltd | £58,833.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |


## R-03: Duplicate-payment indicator in general procurement payment runs [6 (Moderate; Moderate)]

**Audit objective.** Resolve equal-amount payment indicators against genuine invoice obligations and inspect the cited valid-and-undisputed invoice payment term.

**C-03.1. Expected control.** The contract contains the required payment term and valid, undisputed invoices are paid within that term; invoice-level reconciliation identifies whether apparent duplicates are distinct obligations. The duplicate screen is a diagnostic, not a separately quoted prohibition in the rule. [CPR-40] Owner: Not specified in the cited clauses; confirm the operational owner with the council..

**T-03.1. Test.** For every selected group reconcile all listed payments to original invoices, credit notes, ledger postings and the contract. Establish invoice identity, the valid-and-undisputed date, settlement and any reversal. A pass requires distinct supported obligations or a documented correction, and compliance with the sourced invoice-payment term. Equal amounts or payment-run timestamps alone do not establish duplication or lateness; no recovery amount is inferred from the flag. [CPR-40, metric:$.tests.duplicates.same_timestamp.by_tag.general_procurement.groups]  
**Evidence to inspect:** Original invoices, invoice validation/dispute and settlement dates, ledger entries, credit notes and contract payment terms.  
**Sample:** 5 items from `duplicates.csv`, where dominant_tag = general_procurement, tier = same_timestamp, largest gbp_beyond_first first; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:601` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:740` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2134` | 2026-06-18 | SEISMIC SEWAGE SYSTEMS LTD | £5,360.00 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2141` | 2026-06-18 | SEISMIC SEWAGE SYSTEMS LTD | £5,360.00 | Environment |
| 3 | `Over500_2026_P04_-_published.xlsx:3663` | 2026-07-29 | MAISHA STAFFING SOLUTIONS LTD | £3,737.50 | Children's Social Care |
| 3 | `Over500_2026_P04_-_published.xlsx:3894` | 2026-07-29 | MAISHA STAFFING SOLUTIONS LTD | £3,737.50 | Children's Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:2612` | 2026-05-27 | MAISHA STAFFING SOLUTIONS LTD | £2,242.50 | Children's Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:2613` | 2026-05-27 | MAISHA STAFFING SOLUTIONS LTD | £2,242.50 | Children's Social Care |
| 5 | `Over500_2026_P03_-_published.xlsx:2628` | 2026-06-25 | MAISHA STAFFING SOLUTIONS LTD | £2,242.50 | Children's Social Care |
| 5 | `Over500_2026_P03_-_published.xlsx:3361` | 2026-06-25 | MAISHA STAFFING SOLUTIONS LTD | £2,242.50 | Children's Social Care |

**T-03.2. Test.** For every selected group reconcile all listed payments to original invoices, credit notes, ledger postings and the contract. Establish invoice identity, the valid-and-undisputed date, settlement and any reversal. A pass requires distinct supported obligations or a documented correction, and compliance with the sourced invoice-payment term. Equal amounts or payment-run timestamps alone do not establish duplication or lateness; no recovery amount is inferred from the flag. [CPR-40, metric:$.tests.duplicates.different_time.by_tag.general_procurement.groups]  
**Evidence to inspect:** Original invoices, invoice validation/dispute and settlement dates, ledger entries, credit notes and contract payment terms.  
**Sample:** 5 items from `duplicates.csv`, where dominant_tag = general_procurement, tier = different_time, largest gbp_beyond_first first; 12 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:3308` | 2026-07-15 | VolkerHighways Ltd | £101,925.86 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:618` | 2026-07-17 | VolkerHighways Ltd | £101,925.86 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3210` | 2026-07-13 | VolkerHighways Ltd | £54,241.36 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3302` | 2026-07-16 | VolkerHighways Ltd | £54,241.36 | Environment |
| 3 | `Over500_2026_P02_-_published.xlsx:2160` | 2026-05-12 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 3 | `Over500_2026_P02_-_published.xlsx:2161` | 2026-05-13 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 4 | `Over500_2026_P04_-_published.xlsx:3184` | 2026-07-13 | VolkerHighways Ltd | £17,882.35 | Environment |
| 4 | `Over500_2026_P04_-_published.xlsx:3185` | 2026-07-16 | VolkerHighways Ltd | £17,882.35 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:598` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:734` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:789` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:1288` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |


## R-04: Contract extension without visible approval after notice expiry [6 (Moderate; Moderate)]

**Audit objective.** Determine whether payments after the end dates in the public feed relate to a current agreement or an extension approved under the applicable rule.

**C-04.1. Expected control.** Reliance on a contractual extension provision instead of competition requires the designated finance officer approval. [CPR-70] Owner: S.151 Officer..

**T-04.1. Test.** Identify the actual agreement covering each selected payment and reconcile it to the council register. If relying on an extension provision, inspect the original provision and finance officer approval obtained before extension. A pass requires a valid current route and the approval applicable to that route. Record a new agreement separately; an ended public notice does not itself establish a lapsed contract or missing approval. [CPR-70, metric:$.tests.expired_notice_spend.count]  
**Evidence to inspect:** Original agreement and extension provision, approval dated before extension, current register and payment allocation.  
**Sample:** 5 items from `expired_notice_spend.csv`, largest annualised_estimate first, 2 payments per supplier; 7 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:704` | 2026-06-16 | Hope & Clay (Construction) Ltd | £91,306.75 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:58` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £8,250.00 | Development & Housing |
| 2 | `Over500_2026_P03_-_published.xlsx:42` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £6,250.00 | Development & Housing |
| 3 | `Over500_2026_P02_-_published.xlsx:467` | 2026-05-08 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:531` | 2026-06-10 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:459` | 2026-05-15 | CACI Limited | £12,071.67 | Children's Social Care |
| 5 | `Over500_2026_P03_-_published.xlsx:686` | 2026-06-22 | Morton Pattison Ltd | £1,102.00 | Environment |


## R-05: Annualised payment run-rate above the matched award annual rate (variation-control indicator) [9 (High; Medium - High)]

**Audit objective.** Reconcile the payment run-rate indicator to the award scope and establish whether any relevant variation used the required approval route.

**C-05.1. Expected control.** A variation used instead of competition follows the applicable prior written officer or board approval route, supported by the required report and recommendation. [CPR-71, CPR-72] Owner: Monitoring Officer and S.151 Officer; relevant board for the above-threshold route..

**T-05.1. Test.** Inspect every available flagged supplier, anchor the request to sampled payments, and obtain the complete payment schedule and award history. Reconcile payments to the matched award and any other requirements before comparing actual commitments to the approved scope and value. Verify contract dates, whole-term estimate and the annualisation assumptions. For any actual variation, establish the applicable sourced threshold and check prior written officer approval or the board report, recommendation and approval as required. A pass requires either a supported explanation without a variation or the correct variation authority; the run-rate ratio alone is not an overspend or breach. [CPR-71, CPR-72, metric:$.tests.spend_vs_award.count, metric:$.tests.spend_vs_award.parameters.indicator_ratio]  
**Evidence to inspect:** Full award and payment schedule, allocation reconciliation, variation/extension documents, applicable threshold evidence and prior approvals.  
**Sample:** 8 items from `spend_vs_award.csv`, largest ratio first, 2 payments per supplier, (only 8 available); 13 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:905` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £129,125.00 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:492` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £91,629.15 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:396` | 2026-06-10 | BookingLab Limited | £24,000.00 | Transformation, Customer & ICT |
| 3 | `Over500_2026_P03_-_published.xlsx:384` | 2026-06-04 | Exacom Systems Ltd | £12,105.85 | Development & Housing |
| 4 | `Over500_2026_P04_-_published.xlsx:1276` | 2026-07-22 | WCL UK Ltd (Trading as Everything ICT) | £102,882.78 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:276` | 2026-06-30 | SMS-Environmental Ltd | £2,070.00 | Adult Social Care |
| 5 | `Over500_2026_P04_-_published.xlsx:365` | 2026-07-09 | SMS-Environmental Ltd | £1,335.60 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:460` | 2026-05-20 | Softcat Ltd | £8,979.02 | Education & SEND |
| 6 | `Over500_2026_P03_-_published.xlsx:375` | 2026-06-17 | Softcat Ltd | £2,025.98 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P03_-_published.xlsx:371` | 2026-06-08 | IDOX SOFTWARE LTD | £48,579.20 | Community Services |
| 7 | `Over500_2026_P02_-_published.xlsx:462` | 2026-05-20 | IDOX SOFTWARE LTD | £2,647.21 | Development & Housing |
| 8 | `Over500_2026_P03_-_published.xlsx:2130` | 2026-06-09 | TWO SAINTS LTD | £38,775.00 | Development & Housing |
| 8 | `Over500_2026_P04_-_published.xlsx:3181` | 2026-07-22 | TWO SAINTS LTD | £38,775.00 | Development & Housing |


## R-06: Waiver, exception and delegated award-approval documentation visibility gap [6 (Moderate; Moderate)]

**Audit objective.** Determine whether sampled waivers, exceptions and delegated awards have the required prior authority and documented reasons.

**C-06.1. Expected control.** Exceptions and waivers meet permitted grounds, named-approver requirements and advance documentation/reporting, with only the source-permitted urgency treatment. [CPR-17, CPR-18, CPR-19, CPR-20, CPR-21, CPR-22, CPR-23, CPR-24] Owner: Monitoring Officer, S.151 Officer and relevant board/Executive as required by the applicable tier..

**T-06.1. Test.** Obtain the complete waiver/exception log for the review period and reconcile it to procurement award records. Select the five highest-value cases, or all if fewer, covering each approval route represented where possible. For each case establish the permitted ground, total contract value and applicable tier; inspect written reasons, named approvals and report timing. For urgency inspect the precise retrospective-report allowance rather than assuming it waives all prior approval. A pass requires the source-prescribed authority, documentation and timing. If the population or tier cannot be established, record that evidence gap and refer it to the auditor. [CPR-17, CPR-18, CPR-19, CPR-20, CPR-21, CPR-22, CPR-23, CPR-24]  
**Evidence to inspect:** Complete reconciled log, written exceptional grounds, valuation, prior approvals, board/Executive reports and timing.  
**Sample:** Document-only selection pending the complete client log; no waiver records were supplied. The stated targeted selection will be recorded during fieldwork, not fabricated as transaction samples.

**C-06.2. Expected control.** Award decisions use the applicable delegated-authority tier, required report, consultation, recommendations and Key Decision procedures. [CPR-02, CPR-57, CPR-58, CPR-59, CPR-60] Owner: Relevant Service Director, Portfolio Holder, S.151 Officer, Monitoring Officer, relevant boards and Executive as specified by the tier..

**T-06.2. Test.** Obtain the complete award-decision population for the review period and reconcile it to the council contract register. Establish actual total contract value and category, source the applicable statutory parameters, and classify the awards into the cited delegated-authority tiers. The unmatched-notice supplier payments are initial file-request anchors only, not evidence of tier coverage. From the award records select five cases, or all if fewer: take the highest-value case from each represented applicable tier, then fill remaining places by descending total contract value, breaking ties by the stable award reference. Record the selected award references in the fieldwork record. Document absent tiers and any unavailable population, contract valuation, threshold or exact-boundary classification; refer unresolved applicability to the auditor rather than inventing a tier. For each selected award compare the decision-maker, nominations, consultations, written recommendations and board/Executive reports to its actual tier. Where the Key Decision route applies, inspect the required Forward Plan and Call-In trail. A pass requires the correct route supported by contemporaneous records; supplier annualisation is not contract value. [CPR-02, CPR-57, CPR-58, CPR-59, CPR-60]  
**Evidence to inspect:** Complete reconciled award-decision population, actual whole-contract values and categories, sourced thresholds, tier classifications and selection record, delegation/nomination, consultations, recommendations, board reports and Key Decision trail.  
**Sample:** 5 items from `supplier-match.csv`, where dominant_tag = general_procurement, eligible_for_notice_test = True, match_class = ['none', 'near_contain', 'near_ratio'], largest annualised_estimate first, 2 payments per supplier; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:793` | 2026-07-13 | VolkerHighways Ltd | £998,987.64 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:603` | 2026-07-28 | VolkerHighways Ltd | £855,750.25 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2146` | 2026-06-29 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,180,425.32 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:2216` | 2026-06-03 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:665` | 2026-05-15 | The Better Group Ltd | £64,500.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:666` | 2026-05-15 | The Better Group Ltd | £58,833.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |


## R-07: Case-note record-keeping for exempted individual care and education placement choices [6 (Moderate; Moderate)]

**Audit objective.** Establish whether sampled placement payments fall within the cited exemption and, where applicable, have recorded reasons for provider choice and required approval.

**C-07.1. Expected control.** For the defined individual care and education exemption categories, reasons for provider choice are recorded in case notes. Relevant board approval is required where the exempted contract annual or total value exceeds the applicable statutory threshold. [CPR-73, CPR-74] Owner: Service Directors ensure that case-note reasons are recorded; the relevant board approves exempted contracts above the applicable threshold..

**T-07.1. Test.** For each sampled placement-tagged payment obtain a reconciliation to the underlying individual arrangements and establish each arrangement's exemption category from case and contract records. Retain the payment-to-case mapping in the fieldwork record. For each payment anchor select one previously unselected eligible individual arrangement: use the largest attributable payment amount, breaking ties by the stable case reference; if amounts cannot be allocated, use ascending stable case reference and record that allocation limitation. The target is one eligible arrangement per anchor, not one payment counted as an individual case. If an anchor has no eligible case or the mapping cannot be established, record the case-sample shortfall and refer it to the auditor for any additional selection; do not silently replace it or presume missing notes. Inspect contemporaneous case-note reasons for provider choice for each selected eligible arrangement. Establish the annual or total contract value, obtain the sourced applicable statutory threshold and inspect the relevant board approval where that threshold is exceeded. A pass requires the case-note record and any board approval applicable to that arrangement. Unresolved category, threshold or value is an evidence gap for the auditor. [CPR-73, CPR-74, metric:$.population.tags.care_or_education_placement.rows]  
**Evidence to inspect:** Payment-to-individual-arrangement mapping and reproducible case selection record, category and placement decision, dated provider-choice case note, exempted contract, annual or total valuation, sourced applicable threshold and board approval where required.  
**Sample:** 5 items from `spend-clean.csv`, where tag = care_or_education_placement, largest Net amount first, one item per supplier_norm; 5 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:3242` | 2026-07-29 | Engaging Potential Ltd | £272,549.17 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P02_-_published.xlsx:823` | 2026-05-13 | RUSKIN MILL TRUST | £179,236.76 | Adult Social Care |
| 3 | `Over500_2026_P04_-_published.xlsx:3077` | 2026-07-06 | Early Rise Care Ltd. | £126,091.62 | Children's Social Care |
| 4 | `Over500_2026_P04_-_published.xlsx:2729` | 2026-07-22 | PBT SOCIAL CARE LTD | £94,446.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:2124` | 2026-05-27 | Camino Care | £94,040.67 | Children's Social Care |


## Prepared-by-client (PBC) request list

Derived from the test steps above. Each item names the tests that need it.

| # | Risk | Item requested | For tests |
|---|---|---|---|
| 1 | R-01 | Complete procurement files and related commitments for the selected supplier windows; identify the requirement, category, VAT treatment and route. | T-01.1 |
| 2 | R-01 | Quotation invitations, evaluation and award records for the selected near-boundary payments. Include justification and prior Service Director approval for any exceptional award. | T-01.2 |
| 3 | R-02 | Council contract register and publication evidence, award notifications and underlying files for the selected unconfirmed suppliers. | T-02.1 |
| 4 | R-02 | Council portal/CDP invitation and contract notices, timestamps and officer approval for the selected files. | T-02.2 |
| 5 | R-03 | Original invoice, dispute/validation, settlement, ledger and credit-note records for the selected same timestamp groups. | T-03.1 |
| 6 | R-03 | Original invoice, dispute/validation, settlement, ledger and credit-note records for the selected different time groups. | T-03.2 |
| 7 | R-04 | Current contract and register entry, extension provision and prior finance approval for the sampled expired-notice suppliers. | T-04.1 |
| 8 | R-05 | Complete matched-award payment history and schedule, approved variations and the source of the applicable statutory threshold for every flagged award supplier. | T-05.1 |
| 9 | R-06 | Complete reconciled waiver/exception log, case files, reasons, approval records and relevant board/Executive reports for the period. | T-06.1 |
| 10 | R-06 | Complete award-decision population reconciled to the council register, actual contract values and categories, sourced statutory parameters, and award/delegated-authority files for the represented-tier fieldwork selection and initial supplier anchors. | T-06.2 |
| 11 | R-07 | Payment-to-individual-arrangement reconciliation, complete underlying case list for each anchor, attributable payment amounts or stable case references, exemption category and provider-choice case notes, contract valuation and applicable threshold, and relevant board approvals where required. | T-07.1 |
