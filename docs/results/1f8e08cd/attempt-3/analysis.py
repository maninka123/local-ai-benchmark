import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load the datasets
df = pd.read_csv('/output/final_data.csv')
df['transaction_date'] = pd.to_datetime(df['transaction_date'])

# Create output directory for figures
os.makedirs('/output/figures', exist_ok=True)

# --- Analysis 1: Revenue Trend Over Time ---
df['month_year'] = df['transaction_date'].dt.to_period('M').astype(str)
df_monthly = df.groupby('month_year')['revenue'].sum().reset_index()
df_monthly['month_year'] = df_monthly['month_year'].str.replace(' ', '')

plt.figure(figsize=(10, 6))
plt.plot(df_monthly['month_year'], df_monthly['revenue'], marker='o', linestyle='-', color='b')
plt.title('Monthly Revenue Trend (2024-2025)')
plt.xlabel('Month')
plt.ylabel('Revenue (AUD)')
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.savefig('/output/figures/figure_01.png')
plt.close()

# --- Analysis 2: Product Category Performance ---
cat_perf = df.groupby('category').agg({'revenue': 'sum', 'profit': 'sum'}).reset_index()
cat_perf['profit_margin'] = cat_perf['profit'] / cat_perf['revenue']

plt.figure(figsize=(10, 6))
plt.bar(cat_perf['category'], cat_perf['profit'], color='skyblue')
plt.title('Total Profit by Product Category')
plt.xlabel('Category')
plt.ylabel('Profit (AUD)')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--')
plt.tight_layout()
plt.savefig('/output/figures/figure_02.png')
plt.close()

# --- Analysis 3: Regional Revenue vs. Shipping Distance ---
region_map = {val: i for i, val in enumerate(df['region_id'].unique())}
df['region_id_num'] = df['region_id'].map(region_map)

plt.figure(figsize=(10, 6))
plt.scatter(df['shipping_distance_km'], df['revenue'], c=df['region_id_num'], cmap='viridis', alpha=0.5)
plt.colorbar(label='Region ID (Mapped)')
plt.title('Revenue vs. Shipping Distance by Region')
plt.xlabel('Shipping Distance (km)')
plt.ylabel('Revenue (AUD)')
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.savefig('/output/figures/figure_03.png')
plt.close()

# --- Analysis 4: Customer Segment Profitability ---
seg_perf = df.groupby('segment').agg({'revenue': 'sum', 'profit': 'sum'}).reset_index()
seg_perf['profit_margin'] = seg_perf['profit'] / seg_perf['revenue']

plt.figure(figsize=(10, 6))
plt.bar(seg_perf['segment'], seg_perf['profit_margin'], color='salmon')
plt.title('Profit Margin by Customer Segment')
plt.xlabel('Segment')
plt.ylabel('Profit Margin (Fraction)')
plt.grid(axis='y', linestyle='--')
plt.tight_layout()
plt.savefig('/output/figures/figure_04.png')
plt.close()

# --- Analysis 5: Delivery Performance (On-Time vs Service Class) ---
delivery_stats = df.groupby(['service_class', 'on_time'])['delivery_days'].mean().unstack().reset_index()

plt.figure(figsize=(10, 6))
data_cols = [c for c in delivery_stats.columns if c not in ['service_class', 'delivery_days']]
for i, col in enumerate(data_cols):
    plt.plot(delivery_stats['service_class'], delivery_stats[col], label=col, marker='o')

plt.title('Average Delivery Days by Service Class and Status')
plt.xlabel('Service Class')
plt.ylabel('Average Delivery Days')
plt.legend()
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.savefig('/output/figures/figure_05.png')
plt.close()

# --- Analysis 6: Ad Index vs Profit Correlation ---
plt.figure(figsize=(10, 6))
plt.scatter(df['ad_index'], df['profit'], alpha=0.3, color='purple')

x = df['ad_index']
y = df['profit']
m, b = np.polyfit(x, y, 1)
plt.plot(x, m*x + b, color='red', label=f'Trend: y={m:.2f}x+{b:.2f}')

plt.title('Correlation: Ad Index vs. Profit')
plt.xlabel('Ad Index')
plt.ylabel('Profit (AUD)')
plt.legend()
plt.grid(True, linestyle='--')
plt.tight_layout()
plt.savefig('/output/figures/figure_06.png')
plt.close()

# Print summary stats for the report
total_revenue = df['revenue'].sum()
total_profit = df['profit'].sum()
profit_margin = total_profit / total_revenue if total_revenue != 0 else 0
clean_row_count = len(df)
correlation_val = np.corrcoef(x, y)[0,1]

print(f"Total Revenue: {total_revenue:.2f}")
print(f"Total Profit: {total_profit:.2f}")
print(f"Average Profit Margin: {profit_margin:.4f}")
print(f"Clean Row Count: {clean_row_count}")
print(f"Correlation Ad Index vs Profit: {correlation_val:.4f}")
