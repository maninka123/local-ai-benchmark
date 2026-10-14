"""
Comprehensive Business Intelligence Analysis Script
====================================================
This script performs end-to-end data cleaning, analysis, and visualization
for company operational and financial datasets.

Author: Data Science Team
Date: 2024-12-19
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
INPUT_DIR = '/input'
OUTPUT_DIR = '/output'
FIGURES_DIR = os.path.join(OUTPUT_DIR, 'figures')

# Create output directories
os.makedirs(FIGURES_DIR, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
np.random.seed(42)  # For reproducibility

# ============================================================================
# SECTION A: DATA LOADING AND UNDERSTANDING
# ============================================================================

def load_datasets():
    """Load all input datasets."""
    print("=" * 60)
    print("SECTION A: DATA LOADING AND UNDERSTANDING")
    print("=" * 60)
    
    datasets = {
        'transactions': pd.read_csv(os.path.join(INPUT_DIR, 'transactions.csv')),
        'products': pd.read_csv(os.path.join(INPUT_DIR, 'products.csv')),
        'customers': pd.read_csv(os.path.join(INPUT_DIR, 'customers.csv')),
        'regions': pd.read_csv(os.path.join(INPUT_DIR, 'regions.csv')),
        'inventory': pd.read_csv(os.path.join(INPUT_DIR, 'inventory.csv')),
        'operational_events': pd.read_csv(os.path.join(INPUT_DIR, 'operational_events.csv'))
    }
    
    return datasets


def data_quality_assessment(datasets):
    """Perform comprehensive data quality assessment."""
    print("\n--- Data Quality Assessment ---")
    
    quality_report = {}
    
    for name, df in datasets.items():
        print(f"\n{name.upper()}:")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        
        # Missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"  Missing values: {missing[missing > 0].to_dict()}")
        else:
            print(f"  Missing values: None")
        
        # Duplicates
        dup_count = df.duplicated().sum()
        print(f"  Duplicate rows: {dup_count}")
        
        quality_report[name] = {
            'shape': list(df.shape),
            'missing_values': missing[missing > 0].to_dict(),
            'duplicate_count': int(dup_count)
        }
    
    return quality_report


def clean_transactions(transactions_df):
    """Clean and validate transaction data."""
    print("
--- Cleaning Transactions ---")
    
    df = transactions_df.copy()
    
    # Convert date column
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # Remove duplicates based on transaction_id
    initial_count = len(df)
    df = df.drop_duplicates(subset=['transaction_id'])
    removed_dups = initial_count - len(df)
    print(f"  Removed {removed_dups} duplicate transactions")
    
    # Filter invalid quantities (must be positive integers)
    valid_qty = df['quantity'] > 0
    removed_invalid_qty = (~valid_qty).sum()
    df = df[valid_qty]
    print(f"  Removed {removed_invalid_qty} transactions with invalid quantity")
    
    # Filter invalid unit costs (must be positive)
    valid_cost = df['unit_cost'] > 0
    removed_invalid_cost = (~valid_cost).sum()
    df = df[valid_cost]
    print(f"  Removed {removed_invalid_cost} transactions with invalid unit cost")
    
    # Filter invalid revenue (must be positive)
    valid_rev = df['revenue'] > 0
    removed_invalid_rev = (~valid_rev).sum()
    df = df[valid_rev]
    print(f"  Removed {removed_invalid_rev} transactions with invalid revenue")
    
    # Verify margin_pct is within reasonable bounds (0-1)
    valid_margin = (df['margin_pct'] >= 0) & (df['margin_pct'] <= 1)
    removed_invalid_margin = (~valid_margin).sum()
    df = df[valid_margin]
    print(f"  Removed {removed_invalid_margin} transactions with invalid margin")
    
    # Save cleaned data
    output_path = os.path.join(OUTPUT_DIR, 'cleaned_transactions.csv')
    df.to_csv(output_path, index=False)
    print(f"  Saved cleaned transactions to {output_path}")
    
    return df

# ============================================================================
# SECTION B: ANALYTICAL INVESTIGATION
# ============================================================================

def perform_analysis(cleaned_transactions, products, customers, regions, inventory):
    """Perform comprehensive analytical investigation."""
    print("
" + "=" * 60)
    print("SECTION B: ANALYTICAL INVESTIGATION")
    print("=" * 60)
    
    # Merge datasets for analysis
    merged = cleaned_transactions.copy()
    merged['transaction_date'] = pd.to_datetime(merged['transaction_date'])
    merged['month'] = merged['transaction_date'].dt.to_period('M')
    
    merged = merged.merge(products[['product_id', 'category']], on='product_id')
    merged = merged.merge(customers[['customer_id', 'segment']], on='customer_id')
    merged = merged.merge(regions, on='region_id')
    
    analysis_results = {}
    
    # 1. Time Series Analysis - Monthly Revenue
    print("
--- Finding 1: Monthly Revenue Trend ---")
    monthly_revenue = merged.groupby('month')['revenue'].sum().reset_index()
    monthly_revenue['month'] = monthly_revenue['month'].astype(str)
    analysis_results['monthly_revenue'] = monthly_revenue.to_dict('records')
    print(f"  Total Revenue: ${monthly_revenue['revenue'].sum():,.2f}")
    print(f"  Average Monthly Revenue: ${monthly_revenue['revenue'].mean():,.2f}")
    
    # 2. Service Class Performance Analysis
    print("
--- Finding 2: Service Class Performance ---")
    service_perf = merged.groupby('service_class').agg({
        'revenue': ['sum', 'mean'],
        'on_time': 'mean',
        'delivery_days': 'mean'
    }).round(4)
    print(f"  Express On-Time Rate: {service_perf.loc['express', ('on_time', 'mean')]:.2%}")
    print(f"  Standard On-Time Rate: {service_perf.loc['standard', ('on_time', 'mean')]:.2%}")
    analysis_results['service_performance'] = service_perf.to_dict()
    
    # 3. Product Category Margin Analysis
    print("
--- Finding 3: Product Category Margins ---")
    margin_by_cat = merged.groupby('category')['margin_pct'].mean()
    for cat, margin in margin_by_cat.items():
        print(f"  {cat}: {margin:.2%}")
    analysis_results['category_margins'] = margin_by_cat.to_dict()
    
    # 4. Regional Revenue Analysis
    print("
--- Finding 4: Regional Revenue Distribution ---")
    region_rev = merged.groupby('name')['revenue'].sum().sort_values(ascending=True)
    for region, rev in region_rev.items():
        print(f"  {region}: ${rev:,.2f}")
    analysis_results['regional_revenue'] = region_rev.to_dict()
    
    # 5. Inventory Stockout Analysis
    print("
--- Finding 5: Inventory Stockouts ---")
    stockouts_by_prod = inventory.groupby('product_id')['stockouts'].sum()
    total_stockouts = stockouts_by_prod.sum()
    products_with_stockouts = (stockouts_by_prod > 0).sum()
    print(f"  Total Stockout Events: {total_stockouts}")
    print(f"  Products Affected: {products_with_stockouts}")
    analysis_results['stockout_summary'] = {
        'total_events': int(total_stockouts),
        'products_affected': int(products_with_stockouts)
    }
    
    # 6. Customer Segment Analysis
    print("
--- Finding 6: Customer Segment Revenue ---")
    seg_rev = merged.groupby('segment').agg({
        'revenue': 'sum',
        'transaction_id': 'count'
    })
    for segment, data in seg_rev.iterrows():
        print(f"  {segment}: ${data['revenue']:,.2f} ({data['transaction_id']} transactions)")
    analysis_results['segment_revenue'] = seg_rev.to_dict()
    
    return merged, analysis_results
