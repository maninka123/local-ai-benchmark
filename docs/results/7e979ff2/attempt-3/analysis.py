#!/usr/bin/env python3
"""Aurora Instruments - Business Intelligence Analysis Script"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

def load_data():
    df_trans = pd.read_csv("/input/transactions.csv")
    df_cust = pd.read_csv("/input/customers.csv")
    df_prod = pd.read_csv("/input/products.csv")
    df_reg = pd.read_csv("/input/regions.csv")
    df_inv = pd.read_csv("/input/inventory.csv")
    df_events = pd.read_csv("/input/operational_events.csv")
    return {"trans":df_trans,"cust":df_cust,"prod":df_prod,"reg":df_reg,"inv":df_inv,"events":df_events}

def clean_data(data):
    cost_map = dict(zip(data["prod"]["product_id"], data["prod"]["unit_cost"]))
    df_clean = data["trans"].drop_duplicates(subset=["transaction_id"], keep="first")
    df_clean = df_clean[df_clean["quantity"] > 0]
    df_clean["unit_cost_imputed"] = df_clean["unit_cost"].fillna(df_clean["product_id"].map(cost_map))
    df_clean["gross_profit"] = df_clean["revenue"] - (df_clean["quantity"] * df_clean["unit_cost_imputed"])
    df_clean["profit_margin"] = df_clean["gross_profit"] / df_clean["revenue"]
    total_rev = df_clean["revenue"].sum()
    total_prof = df_clean["gross_profit"].sum()
    profit_marg = (total_prof / total_rev) if total_rev > 0 else 0
    cat_rev = df_clean.merge(data["prod"], on="product_id").groupby("category")["revenue"].sum()
    reg_rev = df_clean.merge(data["reg"], on="region_id").groupby("name")["revenue"].sum()
    seg_margin = df_clean.merge(data["cust"][["customer_id","segment"]], on="customer_id").groupby("segment")["profit_margin"].mean()
    return {"clean":df_clean,"metrics":{"total_revenue":round(total_rev,2),"profit_margin":round(profit_marg,4),"clean_row_count":len(df_clean)},"cat_rev":cat_rev,"reg_rev":reg_rev,"seg_margin":seg_margin}
