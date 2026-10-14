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
    'method': 'Time series aggregation and plotting',
    'limitations': 'Missing months with no transactions are omitted; data only covers 2024-2025.',
    'chart': 'figure_01.png'
})

# 2. Product Revenue Distribution
prod_rev = transactions_clean.groupby('product_id')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
plt.figure(figsize=(12,6))
plt.bar(prod_rev['product_id'], prod_rev['revenue'])
plt.title('Revenue by Product')
plt.xlabel('Product ID')
plt.ylabel('Revenue ($)')
plt.xticks(rotation=90)
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_02.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Top Products by Revenue',
    'evidence': f"Top 5 products: {', '.join(prod_rev.head(5)['product_id'])} generating {prod_rev.head(5)['revenue'].sum():,.2f} of total revenue.",
    'method': 'Aggregation and bar chart',
    'limitations': 'Product list limited to those with transactions; seasonal effects not isolated.',
    'chart': 'figure_02.png'
})

# 3. Regional Revenue Share
region_rev = transactions_clean.groupby('region_id')['revenue'].sum().reset_index()
plt.figure(figsize=(8,8))
plt.pie(region_rev['revenue'], labels=region_rev['region_id'], autopct='%1.1f%%', startangle=140)
plt.title('Revenue Share by Region')
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_03.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Revenue Share by Region',
    'evidence': f"Region {region_rev['region_id'].iloc[region_rev['revenue'].idxmax()]} accounts for {region_rev['revenue'].max()/region_rev['revenue'].sum()*100:.1f}% of revenue.",
    'method': 'Aggregation and pie chart',
    'limitations': 'Region definitions may overlap; data only includes transactions with region_id present.',
    'chart': 'figure_03.png'
})

# 4. Customer Segment Performance
cust_seg = transactions_clean.merge(customers[['customer_id','segment']], on='customer_id', how='left')
seg_rev = cust_seg.groupby('segment')['revenue'].sum().reset_index()
plt.figure(figsize=(8,6))
plt.bar(seg_rev['segment'], seg_rev['revenue'])
plt.title('Revenue by Customer Segment')
plt.xlabel('Segment')
plt.ylabel('Revenue ($)')
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_04.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Revenue by Customer Segment',
    'evidence': f"Enterprise segment generated {seg_rev.loc[seg_rev['segment']=='Enterprise','revenue'].values[0]:,.2f}, SMB {seg_rev.loc[seg_rev['segment']=='SMB','revenue'].values[0]:,.2f}, Consumer {seg_rev.loc[seg_rev['segment']=='Consumer','revenue'].values[0]:,.2f}.",
    'method': 'Merge and aggregation',
    'limitations': 'Segment mapping may be incomplete; some customers missing segment info.',
    'chart': 'figure_04.png'
})

# 5. Top 10 Customers
cust_rev = transactions_clean.groupby('customer_id')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
plt.figure(figsize=(12,6))
plt.bar(cust_rev.head(10)['customer_id'], cust_rev.head(10)['revenue'])
plt.title('Top 10 Customers by Revenue')
plt.xlabel('Customer ID')
plt.ylabel('Revenue ($)')
plt.xticks(rotation=45)
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_05.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Top 10 Customers',
    'evidence': f"Top customer {cust_rev.iloc[0]['customer_id']} contributed {cust_rev.iloc[0]['revenue']:,.2f}.",
    'method': 'Aggregation and bar chart',
    'limitations': 'Customer IDs may be duplicated; no demographic context.',
    'chart': 'figure_05.png'
})

# 6. Outlier Transactions
plt.figure(figsize=(10,6))
plt.scatter(transactions_clean['transaction_date'], transactions_clean['revenue'], alpha=0.5)
plt.scatter(outliers['transaction_date'], outliers['revenue'], color='red')
plt.title('Revenue Outliers Over Time')
plt.xlabel('Date')
plt.ylabel('Revenue ($)')
plt.tight_layout()
fig_path = os.path.join(fig_dir, 'figure_06.png')
plt.savefig(fig_path)
plt.close()
findings.append({
    'title': 'Revenue Outliers',
    'evidence': f"Identified {len(outliers)} transactions with revenue > mean + 3*std.",
    'method': 'Statistical outlier detection',
    'limitations': 'Outlier definition may flag legitimate large orders; further review needed.',
    'chart': 'figure_06.png'
})

# Save findings and metrics
output = {
    'metrics': metrics,
    'findings': findings
}
with open(os.path.join(output_dir, 'findings.json'), 'w') as f:
    json.dump(output, f, indent=2)

print('Analysis complete. Figures and findings.json generated.')
