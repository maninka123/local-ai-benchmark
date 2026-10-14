"""Build the complete report and a standalone HTML with embedded PNG figures."""
from pathlib import Path
import base64, html, json, re
O=Path(__file__).resolve().parent
m=json.loads((O/'metrics.json').read_text(encoding='utf-8'))
report='''# Aurora Instruments | Performance investigation

2024–2025 · AUD · Management reference report

## Executive summary

Aurora generated **AUD17.36 million revenue and AUD5.05 million gross profit**, a **29.09% gross margin**, across 24,963 retained completed sales. Revenue declined 1.86% in 2025 despite conspicuous December peaks. The priority is profitable growth: products P00 and P01 generated 20.03% of revenue but together lost AUD6,028 before overheads. Supplier rankings also need correction for service mix: supplier B looks better overall, while A performs better within both express and standard deliveries.

Average delivery time fell after the July 2025 dispatch event, but recorded on-time performance barely changed. This supports investigation of both operational improvement and measurement definitions, rather than a causal success claim. Five implausible prices account for AUD1.985 million of the uncleaned financial total; their exclusion is a disclosed analytical decision requiring invoice confirmation. All results describe the supplied fictional records, not audited financial statements.

## Dataset overview

Every supplied dataset and the data dictionary were examined. Transactions cover every calendar date from 1 January 2024 through 31 December 2025; date coverage alone cannot establish extraction completeness. There are 1,200 customers, 20 products and four regions. All customer joining dates precede this sales window, so acquisition and new-customer growth cannot be evaluated here.

| Dataset | Raw rows | Grain and purpose |
| --- | ---: | --- |
| transactions.csv | 25,000 | Completed sale; transaction_id is the business key |
| products.csv | 20 | Product; category, list price and standard cost |
| customers.csv | 1,200 | Customer; segment, home region and joining date |
| regions.csv | 4 | Region; name, timezone and shipping distance |
| inventory.csv | 480 | Product × month; stock units and stockout counts |
| operational_events.csv | 3 | Dated event; regional or company-wide scope |

Identifier and categorical fields are strings; quantities, flags and inventory measures are integers; prices, revenue, delivery days and advertising index are numeric. Date strings were parsed and validated. Customer, product and region joins are many-to-one; inventory joins only after aggregation to product-month. Every relevant foreign key matched, and joins preserved row counts. Customer home regions agree with transaction regions. The events table uses ALL for company-wide events, which is a scope marker rather than a missing region.

## Data quality assessment

Twenty exact duplicate transaction copies add AUD14,718.41 and are removed once; no conflicting retained business keys remain. Twelve records have quantity −2 and combined revenue −AUD3,301.28. The dictionary explicitly defines completed sales rather than returns, so these rows are quarantined rather than reinterpreted. No other nonpositive quantities occur.

Five records have unit price AUD99,000, or 513–1,500 times their product list prices. All other positive-quantity prices are approximately 1.00 or 1.12 times list. A conservative rule quarantines prices above ten times list: this isolates a clear gap without asserting the true replacement value. These five rows total AUD1,984,950. Keeping them after deduplication and quantity cleaning would produce AUD19,340,397.83 revenue, versus the primary AUD17,355,447.83. This sensitivity is material; finance should resolve the invoices before adopting a statutory total.

Thirty transaction costs are missing. Every observed transaction unit cost equals its product’s catalog cost, supporting a transparent catalog fill for these rows. The filled cost is AUD17,438 on AUD24,128.83 revenue. Omitting those rows instead gives 29.0875% margin, compared with 29.0856% after filling: the aggregate conclusion is insensitive, although actual historical costs remain unverified.

Ten 200-unit orders are retained because prices and revenue arithmetic are consistent with normal transactions. They contribute AUD345,980.40, or 1.99% of revenue; unusual size alone is insufficient grounds for deletion. No missing values occur outside transaction cost. Dimension and inventory keys are unique; date parsing, numeric ranges, foreign keys and revenue identities pass. Stored revenue differs from quantity × price × (1 − discount) by at most half a cent, consistent with currency rounding.

![Figure 7. Transaction anomaly review and financial cleaning sensitivity.](figures/figure_07.png)

## Analytical methodology

Revenue uses the recorded discounted amount after eligibility screening. Gross profit subtracts quantity × effective unit cost; margin is total gross profit divided by total revenue, never an unweighted average of row margins. It excludes freight, marketing, overhead and tax. Delivery rates use retained transaction counts, not revenue weights. Missing values are not treated as zero.

Monthly and annual aggregations investigate time; product, region and customer joins support segment comparisons. Supplier comparisons are stratified by service and standardized to the combined observed service mix. Dispatch comparisons use the stated 1 July 2025 boundary, with a same-year half-year sensitivity. Inventory and sales are matched at product-month grain. Correlations are descriptive Pearson coefficients, without causal interpretation or significance claims. An independent standard-library Decimal implementation rereads the original CSVs and checks financial totals and subgroup numerators separately from pandas.

## Main findings

### 1. December peaks do not establish sustained growth

**Calculated evidence.** Revenue declined from AUD8,759,322.61 in 2024 to AUD8,596,125.22 in 2025; gross profit fell 1.68%, from AUD2,545,357.61 to AUD2,502,578.22. Transactions fell 1.25% and units 1.46%. December revenue was AUD1,238,795.61 and AUD1,290,220.47, respectively: 81.2% and 94.3% above each year’s January–November monthly average.

**Method and significance.** Complete calendar-year totals and within-year monthly baselines distinguish broad performance from seasonal peaks. December transaction counts of 1,784 and 1,805 also exceed January–November averages of 980 and 963. Capacity planning should anticipate the peak while commercial planning addresses flat-to-declining annual sales.

**Limitation.** Only two years are available. The December 2024 campaign event coincides with a peak, but December 2025 peaks too without a recorded campaign event. Seasonality, repeat promotion and other factors cannot be disentangled. Excluding the ten large orders still leaves a 2.07% annual revenue decline.

![Figure 1. Monthly revenue and gross profit, with December observations highlighted.](figures/figure_01.png)

### 2. Two high-revenue products consume the profit opportunity

**Calculated evidence.** Premium’s margin is 7.37%, versus 36.41–36.45% for the other categories. Within Premium, P00 earns only AUD5,289.45 on AUD1,680,219.45 sales; P01 loses AUD11,317.40 on AUD1,796,602.60 sales. Together they account for 2,442 transactions, 20.03% of revenue and negative AUD6,027.95 gross profit. All 1,519 negative-profit transactions involve these two products.

**Method and significance.** Product-level revenue and extended-cost sums reveal that the category label hides substantial variation: P02–P04 remain profitable. At their AUD325 list price and AUD310 cost, P00/P01 break even at only a 4.62% discount before other expenses. Discount governance and supplier-cost negotiations should focus here first.

**Limitation.** North uses higher prices, so the list-price discount threshold is not universal. These calculations do not measure cross-selling, customer lifetime value or strategic reasons for a loss-leading product.

![Figure 2. Category margins and gross profit of the two problematic products.](figures/figure_02.png)

### 3. North’s advantage is closely associated with pricing

**Calculated evidence.** North earns AUD4,781,853.42 revenue and a 34.18% margin; South, East and West earn margins of 26.72%, 27.36% and 27.37%. North’s price-to-list ratio averages almost exactly 1.12, while every retained non-North price equals list. Mean discounts are similar: 7.39% in North versus 7.50% elsewhere.

**Method and significance.** Comparing transaction prices with matched catalog prices uncovers a systematic regional premium. A fixed-volume arithmetic scenario dividing North revenue by 1.12 reduces its margin to 26.28%, illustrating the premium’s accounting importance. Regional margin targets should acknowledge price realization before attributing differences to operating efficiency.

**Limitation.** The scenario is not a forecast: changing prices could change demand, mix or discounting. Regional distance is a single static attribute per region; four regions cannot support a credible causal estimate of shipping-distance effects.

![Figure 3. Regional sales and gross margins under observed prices.](figures/figure_03.png)

### 4. Supplier rankings reverse after controlling service mix

**Observed association.** B’s aggregate on-time rate is 85.22%, compared with A’s 67.45%. Yet A leads within express, 62.46% versus 53.04%, and within standard, 96.65% versus 90.91%. A handles 10,643 express and 1,819 standard transactions; B handles 1,878 express and 10,623 standard transactions.

**Method and significance.** Express represents 85.40% of A’s work and only 15.02% of B’s. Standardizing both suppliers to the combined 50.16% express share yields 79.50% for A and 71.91% for B. This is an aggregate-versus-subgroup reversal, not evidence that B is intrinsically superior. Procurement scorecards should show both workload mix and within-service outcomes.

**Limitation.** Service labels may imply different promises or harder assignments; route, urgency and selection remain uncontrolled. Standardization corrects one measured mix difference, not all confounding. Supplier reassignment effects cannot be estimated from these summaries.

![Figure 4. Aggregate, service-specific and standardized supplier on-time rates.](figures/figure_04.png)

### 5. Faster deliveries do not translate into a clear on-time improvement

**Observed association.** Before July 2025, 18,281 transactions average 3.694 delivery days; the following 6,682 average 2.512, a 1.182-day reduction. On-time rates are nearly unchanged at 76.31% and 76.46%. Comparing only 2025 gives 3.747 versus 2.512 days and 75.77% versus 76.46% on time.

**Method and significance.** Monthly plots and event-boundary comparisons show that delivery time declines in all four regions and both service classes. Express averages fall from 4.463 to 3.253 days; standard from 2.916 to 1.780. The timing is consistent with the dispatch-policy event and merits operational follow-up.

**Limitation.** There is no untreated control group, promised-delivery date or documented on-time threshold. A policy effect is a hypothesis. Faster transit with a stable flag may reflect different service promises or measurement behavior. The East brand-refresh event explicitly states no logistics changes and should not be credited with the company-wide reduction.

![Figure 5. Monthly delivery duration and on-time rate around the dispatch-policy event.](figures/figure_05.png)

### 6. Revenue concentration is modest, but customer profitability differs

**Calculated evidence.** All 1,200 customers transact. The largest customer contributes 0.45% of revenue; the top ten contribute 2.92%, and the top 120 contribute 17.08%. Enterprise, Consumer and SMB revenues are AUD5.887 million, AUD5.834 million and AUD5.634 million, with margins of 28.84%, 29.15% and 29.27%.

**Method and significance.** Customer totals sorted by revenue and segment aggregates show broad participation. However, customer C0501 generates AUD76,157.19 sales and negative AUD1,270.81 gross profit, heavily influenced by its 200-unit P01 order. Retention priorities should consider profit as well as sales rank.

**Limitation.** These are observed purchasing customers, with no leads, inactive account histories or lifetime servicing costs. Arbitrary marketing-group codes do not establish exposure to a controlled campaign.

![Figure 6. Cumulative customer revenue concentration and segment sales.](figures/figure_06.png)

### 7. Inventory and advertising fields do not establish demand drivers

**Calculated evidence and associations.** The 480 product-month records contain 1,590 stockouts; 408 report at least one. Annual counts decline from 816 to 774. Product-month sold units and stockouts have correlation −0.0107; stock units and stockouts have correlation −0.0228. At transaction grain, advertising index and revenue have correlation −0.00665.

**Method and significance.** Aggregating sales before the inventory join prevents repeating stockouts once per transaction. Scatter plots and simple correlations show no strong linear relationship in these measurements. They do not support a quantified stockout-loss estimate or an advertising-return claim.

**Limitation.** Stock timing, replenishment, unmet demand, campaign spend and exposure definitions are absent. Stockouts may suppress observed sales, and product-month aggregation can hide short disruptions. Near-zero correlation is not evidence of no business effect.

![Figure 8. Product-month inventory evidence, without an inferred lost-sales estimate.](figures/figure_08.png)

## Interpretation and limitations

The dataset supports descriptive comparisons and accounting decompositions. It does not support causal policy attribution, audited net profit, inventory turnover or marketing ROI. Unknown extraction completeness, catalog-cost imputation and unresolved extreme prices remain consequential qualifications. Temporal comparisons use transaction date, not dispatch date; event exposure may therefore be imperfect. Deterministic relationships and balanced master tables also reflect the fictional nature of the source and should not be generalized to real operations.

## Operational recommendations

First, finance should resolve the five price anomalies and twelve invalid quantities against source documents, then enforce unique transaction keys, positive sale quantities and required costs. Second, commercial owners should review P00/P01 discount floors and cost terms, testing demand responses before broad repricing. Third, procurement should adopt service-stratified supplier scorecards and track route and promised-date information before changing allocations. Fourth, operations should reconcile on-time definitions with delivery duration and validate the dispatch change using time-aligned orders and appropriate comparison groups. Finally, planning should prepare for December volume while collecting inventory availability and unmet-demand histories. These are recommendations, not measured savings commitments.

## Conclusion

Aurora’s main management opportunity is to protect margin while improving the quality of commercial and operational decisions. The verified records show slightly declining annual sales, a specific premium-product profit leak, a regional price effect and a misleading aggregate supplier comparison. Resolving the financial exceptions and measurement gaps will make those decisions more reliable.

## Reproducibility and evidence

All figures use the supplied data and retained analytical population. Run analysis.py, then build_report.py and verify.py from this output folder with Python and the recorded dependencies. The default data location is the original benchmark datasets/data_analysis directory; analysis.py and verify.py accept --data-dir. Source SHA-256 hashes, field profiles, quarantined rows, filled-cost rows, aggregate tables and structured findings are retained alongside this report. The standalone HTML embeds every chart and uses no external assets. Independent checks and their limits are recorded in the parent verification.json. This is a tool-assisted authored reference, not ground truth or a comparable timed local-model benchmark.
'''
(O/'report.md').write_text(report,encoding='utf-8')

findings=[
 {'id':'F1','title':'Annual decline despite December peaks','kind':'calculated_result','evidence':m['year_over_year']|{'annual':m['groups']['annual'],'december_baselines':m['seasonal']},'method':'Calendar-year sums and December / Jan–Nov monthly mean; large-order sensitivity.','business_significance':'Plan December capacity separately from annual growth.','limitations':['Two years only; campaign attribution unavailable.'],'source_columns':['transactions.transaction_date','transactions.revenue','transactions.quantity','transactions.unit_cost'],'charts':['figures/figure_01.png']},
 {'id':'F2','title':'P00/P01 drive poor Premium profitability','kind':'calculated_result','evidence':m['premium_pair'],'method':'Sum revenue minus extended transaction cost; catalog fill where missing.','business_significance':'Target discount floors and cost negotiation.','limitations':['Excludes overhead and customer lifetime effects.'],'source_columns':['transactions.product_id','transactions.revenue','transactions.quantity','transactions.unit_cost','products.unit_cost','products.category','products.list_price'],'charts':['figures/figure_02.png']},
 {'id':'F3','title':'North price premium accompanies higher margins','kind':'observed_association_and_scenario','evidence':m['region_pricing']|{'regions':m['groups']['region']},'method':'Matched price/list ratios and fixed-volume revenue-divided-by-1.12 scenario.','business_significance':'Adjust regional comparisons for price realization.','limitations':['Scenario holds demand and mix fixed; no causal demand estimate.'],'source_columns':['transactions.region_id','transactions.selling_price','transactions.discount','transactions.revenue','products.list_price','regions.name'],'charts':['figures/figure_03.png']},
 {'id':'F4','title':'Supplier ranking reverses within service','kind':'observed_association','evidence':m['supplier']|{'supplier_service':m['groups']['supplier_service'],'overall':m['groups']['supplier']},'method':'Stratified on-time rates and direct standardization to combined service mix.','business_significance':'Avoid biased aggregate supplier scorecards.','limitations':['Routes, promises and assignment are uncontrolled.'],'source_columns':['transactions.supplier_id','transactions.service_class','transactions.on_time'],'charts':['figures/figure_04.png']},
 {'id':'F5','title':'Delivery duration falls but on-time flags barely improve','kind':'observed_association','evidence':m['delivery']|{'period':m['groups']['period'],'period_service':m['groups']['period_service'],'period_region':m['groups']['period_region']},'method':'Before/after 1 July 2025 and 2025-only sensitivity; monthly patterns.','business_significance':'Check both operational change and measurement consistency.','limitations':['No control group; promises and dispatch dates unavailable.'],'source_columns':['transactions.transaction_date','transactions.delivery_days','transactions.on_time','operational_events.event_date','operational_events.description'],'charts':['figures/figure_05.png']},
 {'id':'F6','title':'Modest concentration with customer profit exceptions','kind':'calculated_result','evidence':m['customer']|{'segments':m['groups']['segment']},'method':'Rank customer revenue totals and reconcile segment aggregates.','business_significance':'Use profitability alongside revenue in account planning.','limitations':['No inactive account or lifetime cost data.'],'source_columns':['transactions.customer_id','transactions.revenue','transactions.quantity','transactions.unit_cost','customers.segment'],'charts':['figures/figure_06.png']},
 {'id':'F7','title':'Inventory and advertising do not establish demand drivers','kind':'observed_correlation','evidence':m['inventory']|m['advertising'],'method':'One-to-one product-month inventory join and Pearson correlations; transaction-level ad correlation.','business_significance':'Collect exposure, replenishment and unmet demand before claiming ROI or lost sales.','limitations':['No causal interpretation; stock timing and spend undefined.'],'source_columns':['inventory.month','inventory.product_id','inventory.stock_units','inventory.stockouts','transactions.quantity','transactions.ad_index','transactions.revenue'],'charts':['figures/figure_08.png']},
 {'id':'F8','title':'Extreme prices materially inflate the untreated total','kind':'data_quality_and_sensitivity','evidence':m['cleaning']|{'retained_large_orders':m['large_orders']},'method':'Exact deduplication, positive completed-sale quantities, >10x catalog-price quarantine, catalog cost fill.','business_significance':'Resolve invoices before using an audited financial baseline.','limitations':['True anomalous prices unverified; large orders plausible rather than externally confirmed.'],'source_columns':['transactions.transaction_id','transactions.quantity','transactions.selling_price','transactions.unit_cost','transactions.revenue','products.list_price','products.unit_cost'],'charts':['figures/figure_07.png']}
]
(O/'findings.json').write_text(json.dumps({'scope':'Supplied fictional 2024–2025 data; AUD','population':m['totals'],'findings':findings,'reference_status':'Self-authored tool-assisted reference; no ground-truth or measured benchmark-score claim'},indent=2,ensure_ascii=False),encoding='utf-8')

def inline(s):
 s=html.escape(s)
 return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)
def slug(s):return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
parts=[]; toc=[]; lines=report.splitlines();i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('# '):i+=1;continue
 if line.startswith('## '):
  title=line[3:];ident=slug(title);toc.append((ident,title));parts.append(f'<h2 id="{ident}">{html.escape(title)}</h2>');i+=1;continue
 if line.startswith('### '):parts.append('<h3>'+inline(line[4:])+'</h3>');i+=1;continue
 if line.startswith('!['):
  match=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line);caption,path=match.groups();encoded=base64.b64encode((O/path).read_bytes()).decode();parts.append(f'<figure><img src="data:image/png;base64,{encoded}" alt="{html.escape(caption)}" loading="eager"><figcaption>{html.escape(caption)} Source: supplied Aurora Instruments datasets; calculations described above.</figcaption></figure>');i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):rows.append([v.strip() for v in lines[i].strip('|').split('|')]);i+=1
  parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[2:])+'</tbody></table></div>');continue
 p=[line];i+=1
 while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','![','|')):p.append(lines[i]);i+=1
 parts.append('<p>'+inline(' '.join(p))+'</p>')
css='''*{box-sizing:border-box}html{scroll-behavior:auto;scroll-padding-top:26px}body{margin:0;background:#f3f6fa;color:#25364b;font:17px/1.7 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:#1769aa;text-decoration:none}a:hover{text-decoration:underline}.hero{background:#fff;border-bottom:1px solid #dce5ed;padding:54px 6vw 40px}.wrap{max-width:1180px;margin:auto}.eyebrow{color:#1769aa;text-transform:uppercase;font-size:12px;font-weight:750;letter-spacing:2px}h1{font-size:clamp(32px,4.4vw,58px);line-height:1.08;max-width:900px;color:#142d4c;margin:16px 0}header p{max-width:720px;color:#607289;margin:14px 0}.badges{display:flex;gap:8px;flex-wrap:wrap}.badge{font-size:12px;padding:4px 10px;border-radius:20px;background:#edf5fa;color:#285e83}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:28px}.card{padding:18px 20px;background:#f5f9fc;border:1px solid #e0eaf2;border-radius:12px}.card span{display:block;font-size:12px;color:#5a6f85}.card b{display:block;font-size:27px;color:#173d63;line-height:1.4}.layout{max-width:1180px;margin:36px auto;display:grid;grid-template-columns:205px minmax(0,1fr);gap:32px;padding:0 20px}aside{align-self:start;position:sticky;top:24px;font-size:12px;line-height:1.55}aside b{display:block;text-transform:uppercase;letter-spacing:1.3px;color:#607289;margin-bottom:12px}aside a{display:block;padding:7px 10px;border-left:2px solid #d9e5ef}article{background:#fff;border:1px solid #e0e7ef;border-radius:16px;padding:34px 42px;min-width:0}h2{font-size:26px;color:#173d63;line-height:1.25;margin:52px 0 18px;padding-top:18px;border-top:1px solid #e4ecf3}h2:first-of-type{margin-top:8px;border-top:0}h3{font-size:21px;line-height:1.35;color:#173d63;margin-top:38px}p{margin:15px 0}strong{font-weight:680;color:#1c3857}figure{margin:28px -18px;background:#fff;border:1px solid #e3eaf1;border-radius:10px;overflow:hidden}figure img{display:block;width:100%;height:auto}figcaption{font-size:12px;line-height:1.5;padding:12px 17px;background:#f7f9fc;color:#607289}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.5}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #e3eaf1}th{background:#edf4f9;color:#234f74}td:nth-child(2){font-variant-numeric:tabular-nums;text-align:right}footer{font-size:12px;color:#64758a;padding:0 24px 40px;text-align:center}.tools{margin-top:22px}.tools button{font:inherit;font-size:13px;border:1px solid #bdcedd;background:white;color:#23557d;border-radius:7px;padding:8px 16px;cursor:pointer}@media(max-width:850px){.layout{display:block;max-width:820px}.cards{grid-template-columns:repeat(2,1fr)}aside{position:static;margin:0 0 24px}aside nav{display:flex;gap:5px;flex-wrap:wrap}aside a{border:1px solid #dae5ee;border-radius:6px;padding:5px 9px}article{padding:24px}figure{margin:24px -10px}}@media(max-width:480px){body{font-size:16px}.hero{padding:32px 22px}.layout{padding:0 10px;margin-top:22px}article{padding:20px 16px}.card{padding:12px}.card b{font-size:23px}h2{font-size:23px}h3{font-size:19px}figure{margin:20px -8px}.table-wrap{margin:0 -6px}}@media print{body{background:white;font-size:11pt}.hero{padding:12px}.layout{display:block;margin:0;padding:0}aside,.tools{display:none}article{border:0;padding:0}figure{break-inside:avoid;max-width:100%;margin:18px 0}h2,h3{break-after:avoid}.cards{grid-template-columns:repeat(4,1fr)}.card b{font-size:19px}footer{padding:12px}}'''
doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>Aurora Instruments — Performance investigation</title><style>'+css+'</style></head><body><header class="hero"><div class="wrap"><div class="eyebrow">Management briefing · 2024–2025</div><h1>Revenue tells only<br>part of the story.</h1><p>A complete investigation of Aurora Instruments: financial performance, operational trade-offs and the data decisions that change the answer.</p><div class="badges"><span class="badge">Fictional data · AUD</span><span class="badge">Six source tables</span><span class="badge">Eight evidence charts</span><span class="badge">Tool-assisted authored reference</span></div><div class="cards"><div class="card"><span>Retained revenue</span><b>$17.36m</b><span>24,963 completed sales</span></div><div class="card"><span>Gross profit</span><b>$5.05m</b><span>29.09% margin</span></div><div class="card"><span>2025 revenue change</span><b>−1.86%</b><span>versus full-year 2024</span></div><div class="card"><span>P00 + P01 gross profit</span><b>−$6,028</b><span>20.03% of revenue</span></div></div><div class="tools"><button type="button" onclick="window.print()">Print / save as PDF</button></div></div></header><div class="layout"><aside aria-label="Report contents"><b>In this report</b><nav>'+''.join(f'<a href="#{ident}">{html.escape(title)}</a>' for ident,title in toc)+'</nav></aside><article>'+''.join(parts)+'</article></div><footer>Self-contained report · Figures and narrative are embedded · Source records retained separately · No measured benchmark score</footer></body></html>'
doc=doc.replace('<figure><img','<figure><button class="chart-open" type="button" aria-label="Expand chart" onclick="openChart(this)"><img').replace('loading="eager"><figcaption>','loading="eager"></button><figcaption>')
doc=doc.replace('<div class="tools"><button type="button" onclick="window.print()">Print / save as PDF</button></div>','<div class="tools">Select any chart to inspect a larger view.</div>')
doc=doc.replace('</style>','.chart-open{display:block;width:100%;border:0;padding:0;background:white;cursor:zoom-in}.chart-open:focus-visible{outline:3px solid #1769aa;outline-offset:-3px}dialog{width:min(1200px,96vw);max-width:96vw;max-height:94vh;border:1px solid #c6d7e4;border-radius:14px;padding:0;box-shadow:0 12px 80px #18355140}dialog::backdrop{background:#132c4c88}.zoom-head{padding:12px 18px;display:flex;justify-content:space-between;align-items:center;gap:14px;font-size:13px;background:#f3f7fa}.zoom-head button{border:1px solid #bdd0e0;border-radius:6px;padding:8px 16px;background:white;color:#173d63;cursor:pointer}.zoom-canvas{overflow:auto;max-height:76vh}.zoom-canvas img{display:block;width:100%;min-width:900px;height:auto}@media print{dialog{display:none}}'+'</style>')
doc=doc.replace('</body>','<dialog id="chart-view" aria-label="Expanded chart"><div class="zoom-head"><span>Expanded chart · scroll horizontally on small screens</span><button type="button" onclick="closeChart()">Close chart</button></div><div class="zoom-canvas" id="zoom-canvas"></div></dialog><script>function openChart(button){const image=button.querySelector("img").cloneNode(true);document.getElementById("zoom-canvas").replaceChildren(image);document.getElementById("chart-view").showModal()}function closeChart(){document.getElementById("chart-view").close();document.getElementById("zoom-canvas").replaceChildren()}</script></body>')
(O/'index.html').write_text(doc,encoding='utf-8')
words=len(re.findall(r"\b[\w’–−]+\b",report))
print(json.dumps({'report_words_approx':words,'embedded_figures':doc.count('data:image/png;base64,'),'html_bytes':len(doc.encode()),'findings':len(findings)}))
