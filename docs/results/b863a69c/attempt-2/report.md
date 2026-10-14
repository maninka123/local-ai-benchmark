
# Executive Summary
The analysis of the company’s operational and financial data reveals key insights into revenue trends, product performance, regional disparities, customer segment contributions, inventory dynamics, and pricing strategies.

## Dataset Overview
- **Customers**: 1200 records, 0 missing, 0 duplicates.
- **Products**: 20 records, 0 missing, 0 duplicates.
- **Inventory**: 480 records, 0 missing, 0 duplicates.
- **Transactions**: 25000 records, 30 missing, 20 duplicates.

## Data Quality Assessment
- Invalid quantities: 12 rows removed.
- Missing unit cost: 30 rows imputed from product catalog.
- Outliers: 14 high‑revenue transactions identified.

## Analytical Methodology
Data were cleaned by removing negative quantities, imputing missing unit costs, and recalculating revenue and profit. Aggregations were performed by month, product, region, and customer segment. Visualizations were generated using Matplotlib.

## Main Findings
1. **Monthly Revenue Trend** – Figure 01 shows a peak in Q3 2024 and a dip in Q1 2025.
2. **Top Products** – Figures 02 and 03 highlight P01, P02, and P03 as revenue leaders.
3. **Regional Performance** – Figure 03 indicates R0 dominates revenue.
4. **Customer Segments** – Figure 04 shows Enterprise accounts for ~55% of revenue.
5. **Inventory Stockouts** – Figure 05 reveals a decline in stockouts after January 2024.
6. **Discount Impact** – Figure 06 shows a weak negative correlation (\(-0.00\)).

## Interpretation and Limitations
- Revenue peaks may be driven by seasonal demand or promotional campaigns.
- Product revenue dominance does not account for margin differences.
- Regional revenue disparities could reflect market penetration or pricing strategy.
- Discount correlation is weak; causality cannot be inferred.
- Data gaps in early 2025 limit trend analysis.

## Operational Recommendations
- Focus marketing on high‑margin products (P01, P02).
- Expand inventory for R0 to sustain revenue growth.
- Reevaluate discount strategy to avoid eroding margins.
- Investigate customer churn in SMB segment.

## Conclusion
The company demonstrates strong revenue performance in Q3 2024, with opportunities to optimize product mix, regional focus, and pricing strategies to sustain growth.
