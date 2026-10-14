#!/usr/bin/env python3
"""Analysis script for company performance investigation."""
import pandas as pd
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Read all CSV files
customers = pd.read_csv('/input/customers.csv')
products = pd.read_csv('/input/products.csv')
regions = pd.read_csv('/input/regions.csv')
inventory = pd.read_csv('/input/inventory.csv')
operational_events = pd.read_csv('/input/operational_events.csv')
transactions = pd.read_csv('/input/transactions.csv')

# Clean data
products_dict = dict(zip(products['product_id'], products['unit_cost']))
transactions_clean = transactions.copy()
transactions_clean['unit_cost'] = transactions_clean['unit_cost'].fillna(transactions_clean['product_id'].map(products_dict))
calculated_revenue = transactions_clean['quantity'] * transactions_clean['selling_price'] * (1 - transactions_clean['discount'])
transactions_clean['revenue'] = calculated_revenue
transactions_clean['cost_of_goods_sold'] = transactions_clean['quantity'] * transactions_clean['unit_cost']
transactions_clean['profit'] = transactions_clean['revenue'] - transactions_clean['cost_of_goods_sold']
transactions_clean['profit_margin'] = (transactions_clean['profit'] / transactions_clean['revenue']).replace([np.inf, -np.inf], 0)

# Merge for analysis
trans_with_region = transactions_clean.merge(regions[['region_id','name']], on='region_id')
trans_with_segment = transactions_clean.merge(customers[['customer_id','segment']], on='customer_id')

# Data quality metrics
duplicates_count = transactions.duplicated().sum()
missing_unit_cost = transactions['unit_cost'].isna().sum()
invalid_quantity = (transactions['quantity'] <= 0).sum()

# Key metrics from cleaned data
total_revenue = transactions_clean['revenue'].sum()
total_profit = transactions_clean['profit'].sum()
profit_margin = (total_profit / total_revenue) if total_revenue > 0 else 0

print(f"Total Revenue: ${total_revenue:,.2f} AUD")
print(f"Total Profit: ${total_profit:,.2f} AUD")
print(f"Overall Profit Margin: {profit_margin*100:.2f}%")
print(f"Clean row count: {len(transactions_clean)}")
print(f"Duplicate rows: {duplicates_count}")
print(f"Missing unit_cost: {missing_unit_cost}")
print(f"Invalid quantity: {invalid_quantity}")
