import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

# --- 1. DATA LOADING ---
print("Loading datasets...")
try:
    df_trans = pd.read_csv('/input/transactions.csv')
    df_prod = pd.read_csv('/input/products.csv')
    df_cust = pd.read_csv('/input/customers.csv')
    df_reg = pd.read_csv('/input/regions.csv')
    df_inv = pd.read_csv('/input/inventory.csv')
    df_ops = pd.read_csv('/input/operational_events.csv')
    print("All datasets loaded successfully.")
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

# --- 2. DATA CLEANING & PREPARATION ---
print("Processing data...")

# Transactions: Clean quantities (must be positive)
# NOTE: Negative margins are kept as business evidence per instructions
original_count = len(df_trans)
df_trans = df_trans[df_trans['quantity'] > 0].copy()
removed_qty = original_count - len(df_trans)

# Calculate financial metrics
if 'selling_price' in df_trans.columns:
    df_trans['total_revenue'] = df_trans['quantity'] * df_trans['selling_price'] * (1 - df_trans['discount'])
else:
    df_trans['total_revenue'] = df_trans['quantity'] * df_trans['unit_price']

df_trans['total_cost'] = df_trans['quantity'] * df_trans['unit_cost']
df_trans['margin'] = df_trans['total_revenue'] - df_trans['total_cost']
df_trans['is_loss'] = df_trans['margin'] < 0

# Merge datasets for analysis
df = df_trans.merge(df_prod, on='product_id', how='left')
df = df.merge(df_cust, on='customer_id', how='left')
df = df.merge(df_reg, on='region_id', how='left')

# Ensure date is datetime
if 'transaction_date' in df.columns:
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df['month'] = df['transaction_date'].dt.to_period('M')

# --- 3. METRICS CALCULATION ---
print("Calculating metrics...")

# Basic Counts
clean_count = len(df)
duplicate_count = original_count - clean_count

# Financials
total_revenue = df['total_revenue'].sum()
total_cost = df['total_cost'].sum()
total_profit = df['margin'].sum()
profit_margin = total_profit / total_revenue if total_revenue > 0 else 0

# Data Quality Issues
missing_cost = df['unit_cost'].isna().sum()
invalid_qty = df[df['quantity'] <= 0].shape[0]
loss_count = df['is_loss'].sum()

# --- 4. VISUALIZATION ---
print("Generating figures...")
os.makedirs('/output/figures', exist_ok=True)

# Figure 1: Monthly Revenue Trend
if 'month' in df.columns:
    monthly_rev = df.groupby('month')['total_revenue'].sum()
    plt.figure(figsize=(12, 6))
    monthly_rev.plot(kind='line', marker='o', color='steelblue')
    plt.title('Monthly Revenue Trend')
    plt.xlabel('Month')
    plt.ylabel('Revenue (USD)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/output/figures/figure_01.png')
    plt.close()

# Figure 2: Top 10 Products by Revenue
product_rev = df.groupby('product_name')['total_revenue'].sum().sort_values(ascending=False).head(10)
plt.figure(figsize=(12, 6))
product_rev.plot(kind='bar', color='steelblue')
plt.title('Top 10 Products by Revenue')
plt.xlabel('Product')
plt.ylabel('Revenue (USD)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('/output/figures/figure_02.png')
plt.close()

# Figure 3: Region Performance
region_rev = df.groupby('name')['total_revenue'].sum().sort_values(ascending=False)
plt.figure(figsize=(10, 6))
region_rev.plot(kind='bar', color='coral')
plt.title('Revenue by Region')
plt.xlabel('Region')
plt.ylabel('Revenue (USD)')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('/output/figures/figure_03.png')
plt.close()

# Figure 4: Margin Distribution
plt.figure(figsize=(10, 6))
df['margin'].hist(bins=50, color='lightgreen', edgecolor='black')
plt.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero Margin')
plt.title('Distribution of Transaction Margins')
plt.xlabel('Margin (USD)')
plt.ylabel('Frequency')
plt.legend()
plt.tight_layout()
plt.savefig('/output/figures/figure_04.png')
plt.close()

# Figure 5: Inventory vs Sales (Scatter)
inv_trans = inventory.merge(transactions[['product_id', 'transaction_date', 'quantity']], on='product_id', how='inner')
inv_trans = inv_trans[inv_trans['quantity'] > 0]

if not inv_trans.empty:
    plt.figure(figsize=(10, 6))
    plt.scatter(inv_trans['stock_level'], inv_trans['quantity'], alpha=0.5)
    plt.title('Inventory Stock Level vs. Sold Quantity')
    plt.xlabel('Stock Level at Sale')
    plt.ylabel('Quantity Sold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/output/figures/figure_05.png')
    plt.close()
else:
    print("Warning: No inventory-sales matches found for Figure 5.")

# Figure 6: Operational Events Count
if 'event_date' in ops.columns:
    ops['event_date'] = pd.to_datetime(ops['event_date'], errors='coerce')
    ops['month'] = ops['event_date'].dt.to_period('M')
    ops_count = ops.groupby('month').size()
    plt.figure(figsize=(12, 6))
    ops_count.plot(kind='bar', color='purple')
    plt.title('Operational Events per Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/output/figures/figure_06.png')
    plt.close()

# --- 5. FINDINGS JSON ---
print("Generating findings.json...")
findings = {
    "metrics": {
        "total_revenue": round(total_revenue, 2),
        "profit_margin": round(profit_margin, 4),
        "clean_row_count": clean_count,
        "duplicate_count": duplicate_count,
        "missing_unit_cost": int(missing_cost),
        "invalid_quantity_count": int(invalid_qty),
        "loss_count": int(loss_count)
    },
    "findings": [
        {
            "title": "Significant Revenue Volatility",
            "evidence": f"Monthly revenue varies by {monthly_rev.std()/monthly_rev.mean()*100:.1f}%",
            "method": "Standard deviation of monthly revenue",
            "business_significance": "High volatility indicates unstable demand or seasonality, requiring flexible inventory planning.",
            "limitations": "Does not explain root causes of volatility."
        },
        {
            "title": "Product Concentration Risk",
            "evidence": f"Top 3 products account for {product_rev.head(3).sum()/total_revenue*100:.1f}% of revenue",
            "method": "Sum of top 3 product revenues",
            "business_significance": "Over-reliance on a few products increases risk if demand drops or supply chains fail.",
            "limitations": "Does not account for product lifecycle or market trends."
        },
        {
            "title": "Regional Performance Disparity",
            "evidence": f"Region {region_rev.idxmax()} generates {region_rev.max()/total_revenue*100:.1f}% of revenue",
            "method": "Revenue aggregation by region",
            "business_significance": "High-performing regions may subsidize underperforming ones; marketing spend should be optimized.",
            "limitations": "Shipping costs and regional taxes are not factored into gross revenue comparison."
        },
        {
            "title": "Margin Analysis and Losses",
            "evidence": f"{loss_count} transactions ({loss_count/clean_count*100:.1f}%) resulted in negative margins.",
            "method": "Count of transactions where margin < 0",
            "business_significance": "Losses represent strategic discounts, clearance sales, or pricing errors that need investigation.",
            "limitations": "Does not distinguish between intentional discounts and operational errors."
        },
        {
            "title": "Data Quality Issues",
            "evidence": f"{missing_cost} missing unit costs and {invalid_qty} invalid quantities found.",
            "method": "Data validation checks",
            "business_significance": "Missing cost data prevents accurate margin analysis and inventory valuation.",
            "limitations": "Missing data may be systematic and require domain knowledge to impute."
        }
    ]
}

with open('/output/findings.json', 'w') as f:
    json.dump(findings, f, indent=2)

print("Analysis complete. Files saved to /output.")