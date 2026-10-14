You are a senior data scientist and business intelligence analyst.

You have received a collection of operational and financial datasets from a fictional company.

Management wants a comprehensive, evidence-based investigation of company performance.

Your objective is to independently examine the data, discover meaningful patterns, identify data quality problems and produce a professional analytical report.

You must complete the following tasks.

**A. Data understanding**

Examine every provided dataset.

Identify:

- Table structures and relationships
- Data types
- Missing values
- Duplicates
- Invalid entries
- Unusual observations
- Potential reliability issues

Explain your cleaning decisions.

**B. Analytical investigation**

Investigate company performance across time, products, regions, customers and operations.

Identify at least five important findings.

For every finding:

- Provide supporting numerical evidence.
- Explain the analytical method.
- State the business significance.
- Identify uncertainty or limitations.

Do not assume that correlation establishes causation.

Investigate unexpected patterns instead of merely reporting obvious averages.

**C. Data visualization**

Create at least six meaningful, high-quality plots.

Select chart types based on the analytical question.

Possible chart categories include:

- Time series
- Comparisons
- Distributions
- Correlations
- Segment-level analysis
- Anomaly visualization

These are suggestions, not mandatory chart types.

Each chart must:

- Use actual dataset values.
- Have readable labels.
- Include units where relevant.
- Include an informative title.
- Avoid misleading scales.
- Support a specific analytical conclusion.

Save all figures to the output directory.

**D. Numerical verification**

Verify key calculations using executable code.

Avoid unsupported estimates.

Clearly distinguish:

- Calculated results
- Observed correlations
- Hypotheses
- Recommendations

**E. Professional report**

Write a detailed professional report of approximately 2,000 words.

Include:

1. Executive summary
2. Dataset overview
3. Data quality assessment
4. Analytical methodology
5. Main findings
6. Supporting charts
7. Interpretation and limitations
8. Operational recommendations
9. Conclusion

Integrate charts into the report.

**F. Final outputs**

Create:

```text
output/
├── report.md
├── analysis.py
├── findings.json
└── figures/
    ├── figure_01.png
    ├── figure_02.png
    └── ...
```

The analysis script must be reproducible.

The JSON file must contain structured findings, their evidence and relevant source columns or chart references.

Do not merely describe how you would perform the analysis.

Execute it and submit actual files.