import pandas as pd
import glob, os
files = {
    'customers': '/input/customers.csv',
    'inventory': '/input/inventory.csv',
    'products': '/input/products.csv',
    'regions': '/input/regions.csv',
    'transactions': '/input/transactions.csv',
    'operational_events': '/input/operational_events.csv'
}
dfs = {k: pd.read_csv(v) for k,v in files.items()}
for name,df in dfs.items():
    print(f'{name}: {df.shape[0]} rows, {df.shape[1]} cols')
    print(df.dtypes)
    print(df.isnull().sum())
