import pandas as pd
import glob
import os

# List of CSV files to analyze
datasets = {
    'customers.csv': 'Customer information',
    'inventory.csv': 'Product inventory levels',
    'operational_events.csv': 'Operational events log',
    'products.csv': 'Product catalog',
    'regions.csv': 'Geographic regions',
    'transactions.csv': 'Sales transactions'
}

# Function to profile a dataset
def profile_csv(file_name, description):
    path = f'/input/{file_name}'
    try:
        df = pd.read_csv(path)
        print(f'=== {description} ({file_name}) ===')
        print('Shape:', df.shape)
        print('Columns:', list(df.columns))
        print('Data types:')
        print(df.dtypes)
        print('Missing values per column:')
        print(df.isnull().sum())
        print('Duplicate rows:', df.duplicated().sum())
        print('---\n')
        # Save profiling summary to a separate file for later reference
        summary = {
            'file': file_name,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_counts': df.isnull().sum().to_dict(),
            'duplicate_count': int(df.duplicated().sum())
        }
        with open(f'/output/profiling_{file_name.replace(".csv", "")}.json', 'w') as f:
            import json
            json.dump(summary, f, indent=2, default=str)
    except Exception as e:
        print(f'Error reading {file_name}: {e}')

# Profile each dataset
for file_name, description in datasets.items():
    profile_csv(file_name, description)
