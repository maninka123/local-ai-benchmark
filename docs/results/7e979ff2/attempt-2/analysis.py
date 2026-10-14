#!/usr/bin/env python3
"""
Aurora Instruments - Comprehensive Business Intelligence Analysis
Reproducible analysis script for financial and operational investigation.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os

def load_data():
    """Load all input datasets."""
    customers = pd.read_csv('/input/customers.csv')
    products = pd.read_csv('/input/products.csv')
    regions = pd.read_csv('/input/regions.csv')
    inventory = pd.read_csv('/input/inventory.csv')
    operational_events = pd.read_csv('/input/operational_events.csv')
    transactions = pd.read_csv('/input/transactions.csv')
    return customers, products, regions, inventory, operational_events, transactions

def clean_transactions(transactions, products):
    """Clean and calculate derived metrics for transactions."""
    transactions_clean = transactions.copy()
    transactions_clean['transaction_date'] = pd.to_datetime(transactions_clean['transaction_date'])
    transactions_clean['unit_cost'] = transactions_clean['unit_cost'].fillna(
        transactions_clean['product_id'].map(dict(zip(products['product_id'], products['unit_cost'])))
    )
    calculated_revenue = transactions_clean['quantity'] * transactions_clean['selling_price'] * (1 - transactions_clean['discount'])
    transactions_clean['revenue'] = calculated_revenue
    calculated_cost = transactions_clean['quantity'] * transactions_clean['unit_cost']
    transactions_clean['cost_of_goods_sold'] = calculated_cost
    calculated_profit = transactions_clean['revenue'] - calculated_cost
    transactions_clean['profit'] = calculated_profit
    calculated_margin = (calculated_profit / transactions_clean['revenue']).replace([np.inf, -np.inf], 0)
    transactions_clean['profit_margin'] = calculated_margin
    
    # Remove duplicates and invalid quantities
    transactions_clean = transactions_clean.drop_duplicates(subset=['transaction_id'], keep='first')
    valid_transactions = transactions_clean[transactions_clean['quantity'] > 0].copy()
    return valid_transactions

def calculate_metrics(valid_transactions, products, regions, customers):
    """Calculate key business metrics."""
    total_revenue = valid_transactions['revenue'].sum()
    total_profit = valid_transactions['profit'].sum()
    profit_margin = (total_profit / total_revenue) if total_revenue > 0 else 0
    
    category_revenue = valid_transactions.merge(products, on='product_id').groupby('category')['revenue'].sum()
    region_revenue = valid_transactions.merge(regions, on='region_id').groupby('name')['revenue'].sum()
    segment_margin = valid_transactions.merge(customers[['customer_id','segment']], on='customer_id').groupby('segment')['profit_margin'].mean()
    
    return {
        'total_revenue': total_revenue,
        'total_profit': total_profits,
        'profit_margin': profit_margin,
        'category_revenue': category_revenue,
        'region_revenue': region_revenue,
        'segment_margin': segment_margin
    }

def create_figures(valid_transactions, products, regions, customers, inventory):
    """Create all six analytical figures."""
    os.makedirs('/output/figures', exist_ok=True)
    
    # FIGURE 1: Revenue by Product Category
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    category_revenue = valid_transactions.merge(products, on='product_id').groupby('category')['revenue'].sum()
    category_revenue_sorted = category_revenue.sort_values(ascending=False)
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
    ax1.barh(category_revenue_sorted.index, category_revenue_sorted.values, color=colors[:len(category_revenue_sorted)])
    ax1.set_xlabel('Revenue (AUD)')
    ax1.set_ylabel('Product Category')
    ax1.set_title('Revenue by Product Category - Aurora Instruments 2024-2025', fontsize=14)
    ax1.tick_params(axis='x', rotation=90)
    ax1.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    fig1.savefig('/output/figures/figure_01.png', dpi=150, bbox_inches='tight')
    plt.close(fig1)
    
    # FIGURE 2: Revenue by Region
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    region_revenue = valid_transactions.merge(regions, on='region_id').groupby('name')['revenue'].sum()
    ax2.pie(region_revenue.values, labels=region_revenue.index, autopct='%1.1f%%', startangle=90, colors=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'])
    ax2.set_title('Revenue Distribution by Region - Aurora Instruments 2024-2025', fontsize=14)
    plt.tight_layout()
    fig2.savefig('/output/figures/figure_02.png', dpi=150, bbox_inches='tight')
    plt.close(fig2)
    
    # FIGURE 3: Profit Margin by Customer Segment
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    segment_margin = valid_transactions.merge(customers[['customer_id','segment']], on='customer_id').groupby('segment')['profit_margin'].mean()
    ax3.bar(segment_margin.index, segment_margin.values * 100, color=['#2ecc71', '#3498db', '#e74c3c'])
    ax3.set_xlabel('Customer Segment')
    ax3.set_ylabel('Average Profit Margin (%)')
    ax3.set_title('Average Profit Margin by Customer Segment', fontsize=14)
    ax3.tick_params(axis='x', rotation=0)
    ax3.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig3.savefig('/output/figures/figure_03.png', dpi=150, bbox_inches='tight')
    plt.close(fig3)
    
    # FIGURE 4: Monthly Revenue Trend
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    monthly_revenue = valid_transactions.groupby(valid_transactions['transaction_date'].dt.to_period('M')).agg({'revenue': 'sum'})
    monthly_revenue_sorted = monthly_revenue.sort_index()
    ax4.plot(monthly_revenue_sorted.index.astype(str), monthly_revenue_sorted['revenue'], marker='o', linewidth=2, color='#3498db')
    ax4.set_xlabel('Month (YYYY-MM)')
    ax4.set_ylabel('Revenue (AUD)')
    ax4.set_title('Monthly Revenue Trend - Aurora Instruments 2024-2025', fontsize=14)
    ax4.grid(alpha=0.3)
    plt.tight_layout()
    fig4.savefig('/output/figures/figure_04.png', dpi=150, bbox_inches='tight')
    plt.close(fig4)
    
    # FIGURE 5: Inventory Stockouts by Product
    fig5, ax5 = plt.subplots(figsize=(12, 6))
    stockout_by_product = inventory.groupby('product_id')['stockouts'].sum().sort_values(ascending=False)
    ax5.barh(stockout_by_product.index, stockout_by_product.values, color='#e74c3c')
    ax5.set_xlabel('Total Stockouts (units)')
    ax5.set_ylabel('Product ID')
    ax5.set_title('Inventory Stockouts by Product - Aurora Instruments 2024-2025', fontsize=14)
    ax5.tick_params(axis='x', rotation=90)
    ax5.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    fig5.savefig('/output/figures/figure_05.png', dpi=150, bbox_inches='tight')
    plt.close(fig5)
    
    # FIGURE 6: Discount vs Profit Margin Scatter Plot
    fig6, ax6 = plt.subplots(figsize=(12, 8))
    scatter_data = valid_transactions.merge(products, on='product_id').merge(customers[['customer_id','segment']], on='customer_id')
    ax6.scatter(scatter_data['discount'], scatter_data['profit_margin']*100, alpha=0.6, c=scatter_data['segment'].map({'Consumer': '#2ecc71', 'Enterprise': '#3498db', 'SMB': '#e74c3c'}), cmap='viridis')
    ax6.set_xlabel('Discount (%)')
    ax6.set_ylabel('Profit Margin (%)')
    ax6.set_title('Discount vs Profit Margin by Customer Segment', fontsize=14)
    ax6.grid(alpha=0.3)
    plt.tight_layout()
    fig6.savefig('/output/figures/figure_06.png', dpi=150, bbox_inches='tight')
    plt.close(fig6)
    
    print("All 6 figures saved successfully!")

if __name__ == "__main__":
    customers, products, regions, inventory, operational_events, transactions = load_data()
    valid_transactions = clean_transactions(transactions, products)
    metrics = calculate_metrics(valid_transactions, products, regions, customers)
    create_figures(valid_transactions, products, regions, customers, inventory)
