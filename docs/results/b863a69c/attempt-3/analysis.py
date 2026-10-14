import pandas as pd, numpy as np, matplotlib.pyplot as plt, os, json

input_dir = '/input'
output_dir = '/output'
fig_dir = os.path.join(output_dir, 'figures')
os.makedirs(fig_dir, exist_ok=True)

# Load data
customers = pd.read_csv(os.path.join(input_dir, 'customers.csv'))
products = pd.read_csv(os.path.join(input_dir, 'products.csv'))
inventory = pd.read_csv(os.path.join(input_dir, 'inventory.csv'))
regions = pd.read_csv(os.path.join(input_dir, 'regions.csv')) if os.path.exists(os.path.join(input_dir, 'regions.csv')) else pd.DataFrame()
transactions = pd.read_csv(os.path.join(input_dir, 'transactions.csv'))

# Data understanding metrics
metrics = {
    'customers_rows': int(len(customers)),
    'customers_missing': int(customers.isna().sum().sum()),
    'customers_duplicates': int(customers.duplicated().sum()),
    'products_rows': int(len(products)),
    'products_missing': int(products.isna().sum().sum()),
    'products_duplicates': int(products.duplicated().sum()),
    'inventory_rows': int(len(inventory)),
    'inventory_missing': int(inventory.isna().sum().sum()),
    'inventory_duplicates': int(inventory.duplicated().sum()),
    'transactions_rows': int(len(transactions)),
    'transactions_missing': int(transactions.isna().sum().sum()),
    'transactions_duplicates': int(transactions.duplicated().sum()),
}

# Identify invalid entries
invalid_qty = transactions[transactions['quantity'] < 0]
metrics['invalid_quantity_count'] = int(len(invalid_qty))
missing_unit_cost = transactions[transactions['unit_cost'].isna()]
metrics['missing_unit_cost'] = int(len(missing_unit_cost))

# Clean data
transactions_clean = transactions.copy()
# Remove negative quantity
transactions_clean = transactions_clean[transactions_clean['quantity'] >= 0]
# Merge unit_cost from products if missing
transactions_clean = transactions_clean.merge(products[['product_id','unit_cost']], on='product_id', how='left', suffixes=('','_prod'))
transactions_clean['unit_cost'] = transactions_clean['unit_cost'].fillna(transactions_clean['unit_cost_prod'])
transactions_clean.drop(columns=['unit_cost_prod'], inplace=True)
# Recalculate revenue and profit
transactions_clean['revenue'] = transactions_clean['quantity'] * transactions_clean['selling_price'] * (1 - transactions_clean['discount'])
transactions_clean['profit'] = transactions_clean['revenue'] - transactions_clean['quantity'] * transactions_clean['unit_cost']

# Aggregate metrics
metrics['total_revenue'] = float(transactions_clean['revenue'].sum())
metrics['profit_margin'] = float(transactions_clean['profit'].sum() / metrics['total_revenue']) if metrics['total_revenue'] else np.nan
metrics['clean_row_count'] = int(len(transactions_clean))
metrics['duplicate_count'] = int(transactions_clean.duplicated().sum())
# Outliers: revenue > mean + 3*std
outliers = transactions_clean[transactions_clean['revenue'] > transactions_clean['revenue'].mean() + 3*transactions_clean['revenue'].std()]
metrics['entry_outlier_count'] = int(len(outliers))

# Prepare findings list
findings = []

# 1. Monthly Revenue Trend
transactions_clean['transaction_date'] = pd.to_datetime(transactions_clean['transaction_date'])
rev_time = transactions_clean.groupby(transactions_clean['transaction_date'].dt.to_period('M'))['revenue'].sum().reset_index()
rev_time['transaction_date'] = rev_time['transaction_date'].dt.to_timestamp()
plt.figure(figsize=(10,6))
plt.plot(rev_time['transaction_date'], rev_time['revenue'], marker='o')
plt.title('Monthly Revenue Trend')
plt.xlabel('Month')
plt.ylabel('Revenue ($)')
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_01.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Monthly Revenue Trend',
    'evidence': f"Peak revenue in {rev_time['transaction_date'].iloc[rev_time['revenue'].idxmax()].strftime('%B %Y')} with ${rev_time['revenue'].max():,.2f}. Lowest in {rev_time['transaction_date'].iloc[rev_time['revenue'].idxmin()].strftime('%B %Y')} with ${rev_time['revenue'].min():,.2f}.",
    'method': 'Time series aggregation of revenue by month.',
    'limitations': 'Missing data for some months due to incomplete transaction logs.',
    'source_columns': ['transaction_date', 'revenue'],
    'charts': ['figure_01.png']
})

# 2. Top 10 Products by Revenue
prod_rev = transactions_clean.groupby('product_id')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
plt.figure(figsize=(10,6))
plt.bar(prod_rev['product_id'][:10], prod_rev['revenue'][:10])
plt.title('Top 10 Products by Revenue')
plt.xlabel('Product ID')
plt.ylabel('Revenue ($)')
plt.xticks(rotation=45)
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_02.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Top 10 Products by Revenue',
    'evidence': f"Products {', '.join(prod_rev['product_id'][:3])} dominate revenue, accounting for {prod_rev['revenue'][:3].sum()/metrics['total_revenue']*100:.1f}% of total.",
    'method': 'Aggregation of revenue per product.',
    'limitations': 'Does not account for profit margins per product.',
    'source_columns': ['product_id', 'revenue'],
    'charts': ['figure_02.png']
})

# 3. Revenue by Region
if not regions.empty:
    trans_reg = transactions_clean.merge(regions[['region_id','region_name']], on='region_id', how='left')
    reg_rev = trans_reg.groupby('region_name')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
    plt.figure(figsize=(10,6))
    plt.bar(reg_rev['region_name'], reg_rev['revenue'])
    plt.title('Revenue by Region')
    plt.xlabel('Region')
    plt.ylabel('Revenue ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig_path = os.path.join(fig_dir, 'figure_03.png')
    plt.savefig(fig_path)
    plt.close()
    findings.append({
        'title': 'Revenue by Region',
        'evidence': f"Region {reg_rev['region_name'].iloc[0]} leads revenue with ${reg_rev['revenue'].iloc[0]:,.2f}, while {reg_rev['region_name'].iloc[-1]} lags with ${reg_rev['revenue'].iloc[-1]:,.2f}.",
        'method': 'Group by region_name.',
        'limitations': 'Region mapping may be incomplete.',
        'source_columns': ['region_name', 'revenue'],
        'charts': ['figure_03.png']
    })

# 4. Revenue Share by Customer Segment
if 'segment' in customers.columns:
    trans_seg = transactions_clean.merge(customers[['customer_id','segment']], on='customer_id', how='left')
    seg_rev = trans_seg.groupby('segment')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
    plt.figure(figsize=(10,6))
    plt.bar(seg_rev['segment'], seg_rev['revenue'])
    plt.title('Revenue Share by Customer Segment')
    plt.xlabel('Segment')
    plt.ylabel('Revenue ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig_path = os.path.join(fig_dir, 'figure_04.png')
    plt.savefig(fig_path)
    plt.close()
    findings.append({
        'title': 'Revenue Share by Customer Segment',
        'evidence': f"Enterprise segment accounts for {seg_rev['revenue'].iloc[0]/metrics['total_revenue']*100:.1f}% of revenue.",
        'method': 'Merge and aggregate.',
        'limitations': 'Segment assignment may be outdated.',
        'source_columns': ['segment', 'revenue'],
        'charts': ['figure_04.png']
    })

# 5. Monthly Stockouts Trend
if not inventory.empty:
    inv_stock = inventory.copy()
    inv_stock['month'] = pd.to_datetime(inv_stock['date']).dt.to_period('M').dt.to_timestamp()
    stock_month = inv_stock.groupby('month')['stockouts'].sum().reset_index()
    plt.figure(figsize=(10,6))
    plt.bar(stock_month['month'], stock_month['stockouts'])
    plt.title('Monthly Stockouts Trend')
    plt.xlabel('Month')
    plt.ylabel('Stockouts')
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig_path = os.path.join(fig_dir, 'figure_05.png')
    plt.savefig(fig_path)
    plt.close()
    findings.append({
        'title': 'Monthly Stockouts Trend',
        'evidence': f"Stockouts peaked in {stock_month['month'].iloc[0].strftime('%B %Y')} with {stock_month['stockouts'].iloc[0]} events.",
        'method': 'Aggregation of stockouts per month.',
        'limitations': 'Stockouts may not reflect actual demand.',
        'source_columns': ['month', 'stockouts'],
        'charts': ['figure_05.png']
    })

# 6. Discount vs Revenue Correlation
plt.figure(figsize=(8,6))
plt.scatter(transactions_clean['discount'], transactions_clean['revenue'], alpha=0.5)
plt.title('Discount vs Revenue')
plt.xlabel('Discount')
plt.ylabel('Revenue ($)')
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_06.png')
plt.savefig(fig_path)
plt.close()
corr = transactions_clean['discount'].corr(transactions_clean['revenue'])
findings.append({
    'title': 'Discount vs Revenue Correlation',
    'evidence': f"Correlation coefficient: {corr:.2f}",
    'method': 'Scatter plot and Pearson correlation.',
    'limitations': 'Correlation does not imply causation; other factors may influence revenue.',
    'source_columns': ['discount', 'revenue'],
    'charts': ['figure_06.png']
})

# Write findings.json
output = {'metrics': metrics, 'findings': findings}
with open(os.path.join(output_dir, 'findings.json'), 'w') as f:
    json.dump(output, f, indent=2)

print('Analysis complete. Findings written to findings.json')
