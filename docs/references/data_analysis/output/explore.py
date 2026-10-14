from pathlib import Path
import pandas as pd, json
ROOT=Path(__file__).resolve().parents[5]
D=ROOT/'datasets/data_analysis'
tables={p.stem:pd.read_csv(p) for p in D.glob('*.csv')}
for name,df in tables.items():
 print('\nTABLE',name,df.shape,'duplicates',df.duplicated().sum())
 print(df.dtypes.to_string()); print(df.describe(include='all').to_string())
 print('KEY DUP',df.duplicated(subset=list(df.columns[:1])).sum())
t=tables['transactions']; p=tables['products']
print('duplicate IDs', t[t.transaction_id.duplicated(False)].to_string(index=False))
print('bad numeric',t[(t.quantity<=0)|(t.selling_price<=0)|(t.discount<0)|(t.discount>1)|(t.unit_cost<0)|(t.revenue<0)|(t.delivery_days<0)|(~t.on_time.isin([0,1]))].to_string(index=False))
e=t.quantity*t.selling_price*(1-t.discount)
print('revenue mismatches',t[(e-t.revenue).abs()>.011].to_string(index=False))
for table,key in [('products','product_id'),('customers','customer_id'),('regions','region_id')]:
 print('unmatched',key,t.loc[~t[key].isin(tables[table][key])].to_string(index=False))
print('all products',p.to_string(index=False))
