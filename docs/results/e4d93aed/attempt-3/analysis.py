import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

np.random.seed(42)
os.makedirs('/output/figures', exist_ok=True)

print("=" * 60)
print("LOADING DATASETS")
print("=" * 60)

input_dir = '/input'
output_dir = '/output'

transactions = pd.read_csv(os.path.join(input_dir, 'transactions.csv'))
products = pd.read_csv(os.path.join(input_dir, 'products.csv'))
customers = pd.read_csv(os.path.join(input_dir, 'customers.csv'))
regions = pd.read_csv(os.path.join(input_dir, 'regions.csv'))
inventory = pd.read_csv(os.path.join(input_dir, 'inventory.csv'))
events = pd.read_csv(os.path.join(input_dir, 'operational_events.csv'))

print(f"Transactions: {transactions.shape}")
print(f"Products: {products.shape}")
print(f"Customers: {customers.shape}")
print(f"Regions: {regions.shape}")
print(f"Inventory: {inventory.shape}")
print(f"Events: {events.shape}")

print("\n" + "=" * 60)
print("DATA QUALITY ASSESSMENT")
print("=" * 60)

data_quality = {
    'raw_transactions': len(transactions),
    'duplicate_transaction_ids': int(transactions.duplicated(subset=['transaction_id']).sum()),
    'missing_unit_cost': int(transactions['unit_cost'].isnull().sum()),
    'invalid_quantity': int((transactions['quantity'] <= 0).sum()),
    'invalid_revenue': int((transactions['revenue'] <= 0).sum())
}

print(f"Duplicate transaction_ids: {data_quality['duplicate_transaction_ids']}")
print(f"Missing unit_cost values: {data_quality['missing_unit_cost']}")
print(f"Invalid quantity (<=0): {data_quality['invalid_quantity']}")
print(f"Invalid revenue (<=0): {data_quality['invalid_revenue']}")

print("\n" + "=" * 60)
print("DATA CLEANING")
print("=" * 60)

df = transactions.copy()
initial_count = len(df)

df = df.drop_duplicates(subset=['transaction_id'], keep='first')
removed_dups = initial_count - len(df)
print(f"After removing {removed_dups} duplicates: {len(df)} rows")

df = df[df['quantity'] > 0]
removed_qty = (initial_count - removed_dups) - len(df)
print(f"After removing {removed_qty} invalid quantity records: {len(df)} rows")

df = df[df['unit_cost'] > 0]
removed_cost = (initial_count - removed_dups) - len(df)
print(f"After removing {removed_cost} invalid unit_cost records: {len(df)} rows")

df = df[df['revenue'] > 0]
removed_rev = (initial_count - removed_dups) - len(df)
print(f"After removing {removed_rev} invalid revenue records: {len(df)} rows")

df.to_csv(os.path.join(output_dir, 'cleaned_transactions.csv'), index=False)
print(f"\nCleaned transactions saved: {len(df)} rows")

print("\n" + "=" * 60)
print("DATA MERGING")
print("=" * 60)

df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df = df.merge(products[['product_id', 'category']], on='product_id', how='left')
df = df.merge(customers[['customer_id', 'segment']], on='customer_id', how='left')
df = df.merge(regions, on='region_id', how='left')
print(f"Merged dataset: {df.shape}")

df['total_cost'] = df['quantity'] * df['unit_cost']
df['profit'] = df['revenue'] - df['total_cost']
df['margin_pct'] = df['profit'] / df['revenue']
df['year_month'] = df['transaction_date'].dt.strftime('%Y-%m')

print("\n" + "=" * 60)
print("FINANCIAL METRICS")
print("=" * 60)

total_revenue = float(df['revenue'].sum())
total_profit = float(df['profit'].sum())
average_margin = float(df['margin_pct'].mean())
cleaned_row_count = len(df)

print(f"Total Revenue: ${total_revenue:,.2f}")
print(f"Total Profit: ${total_profit:,.2f}")
print(f"Average Margin: {average_margin:.4f} ({average_margin*100:.2f}%)")
print(f"Cleaned Row Count: {cleaned_row_count}")

print("\n" + "=" * 60)
print("GENERATING VISUALIZATIONS")
print("=" * 60)

import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Figure 1: Monthly Revenue Time Series
fig1, ax1 = plt.subplots(figsize=(14, 6))
monthly_data = df.groupby('year_month').agg({'revenue': 'sum', 'profit': 'sum'}).reset_index()
ax1.plot(monthly_data['year_month'], monthly_data['revenue']/1e6, marker='o', linewidth=2, label='Revenue')
ax1.plot(monthly_data['year_month'], monthly_data['profit']/1e6, marker='s', linewidth=2, label='Profit')
ax1.set_xlabel('Month')
ax1.set_ylabel('Amount (Millions USD)')
ax1.set_title('Monthly Revenue and Profit Trend (2024)', fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.tight_layout()
fig1.savefig('/output/figures/figure_01.png', dpi=150)
plt.close(fig1)
print("Figure 1: Monthly Revenue and Profit - saved")

# Figure 2: Category Margin Comparison
fig2, ax2 = plt.subplots(figsize=(12, 6))
category_stats = df.groupby('category').agg({'revenue': 'sum', 'margin_pct': 'mean'}).reset_index()
category_stats = category_stats.sort_values('margin_pct')
bars = ax2.barh(category_stats['category'], category_stats['margin_pct']*100, color='steelblue')
ax2.set_xlabel('Margin Percentage (%)')
ax2.set_ylabel('Category')
ax2.set_title('Average Margin by Product Category', fontsize=14)
ax2.axvline(x=average_margin*100, color='red', linestyle='--', label=f'Overall Avg: {average_margin*100:.1f}%')
ax2.legend()
for bar, margin in zip(bars, category_stats['margin_pct']):
    ax2.text(margin*100 + 0.5, bar.get_y() + bar.get_height()/2, f'{margin*100:.1f}%', va='center', fontsize=9)
plt.tight_layout()
fig2.savefig('/output/figures/figure_02.png', dpi=150)
plt.close(fig2)
print("Figure 2: Category Margin Comparison - saved")

# Figure 3: Regional Performance
fig3, ax3 = plt.subplots(figsize=(12, 6))
region_stats = df.groupby('name').agg({'revenue': 'sum', 'margin_pct': 'mean'}).reset_index()
x = np.arange(len(region_stats))
width = 0.35
ax3.bar(x - width/2, region_stats['revenue']/1e6, width, label='Revenue (M USD)', alpha=0.8)
ax3_twin = ax3.twinx()
ax3_twin.bar(x + width/2, region_stats['margin_pct']*100, width, label='Margin (%)', color='orange', alpha=0.8)
ax3.set_xlabel('Region')
ax3.set_ylabel('Revenue (Millions USD)')
ax3_twin.set_ylabel('Margin (%)')
ax3.set_title('Regional Revenue and Margin Performance', fontsize=14)
ax3.set_xticks(x)
ax3.set_xticklabels(region_stats['name'])
for i, (rev, margin) in enumerate(zip(region_stats['revenue']/1e6, region_stats['margin_pct']*100)):
    ax3.text(i - width/2, rev + 0.05, f'${rev:.1f}M', ha='center', fontsize=8)
    ax3_twin.text(i + width/2, margin + 0.5, f'{margin:.1f}%', ha='center', fontsize=8)
plt.tight_layout()
fig3.savefig('/output/figures/figure_03.png', dpi=150)
plt.close(fig3)
print("Figure 3: Regional Performance - saved")
