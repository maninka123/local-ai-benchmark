"""Reproducible business data; answers are written only to evaluation_private."""
import numpy as np, pandas as pd, hashlib, json
from benchmark.util import ROOT, write_json

def reference(directory):
    t=pd.read_csv(directory/'transactions.csv'); p=pd.read_csv(directory/'products.csv')
    raw=t.copy(); duplicates=int(t.duplicated('transaction_id').sum()); missing=int(t.unit_cost.isna().sum())
    invalid=int((t.quantity<=0).sum()); entry=int((t.selling_price>10000).sum())
    t=t.drop_duplicates('transaction_id');t=t[(t.quantity>0)&(t.selling_price<=10000)].copy()
    t['unit_cost']=t.unit_cost.fillna(t.product_id.map(p.set_index('product_id').unit_cost))
    t['profit']=t.revenue-t.quantity*t.unit_cost;t['month']=t.transaction_date.str[:7]
    supplier=t.groupby(['service_class','supplier_id']).on_time.mean().unstack()
    overall=t.groupby('supplier_id').on_time.mean()
    metrics={'duplicate_count':duplicates,'missing_unit_cost':missing,'invalid_quantity_count':invalid,
        'entry_outlier_count':entry,'clean_row_count':len(t),'total_revenue':float(t.revenue.sum()),
        'profit_margin':float(t.profit.sum()/t.revenue.sum()),
        'december_mean_revenue':float(t[t.transaction_date.str[5:7]=='12'].groupby('month').revenue.sum().mean()),
        'premium_margin':float(t[t.product_id.isin(['P00','P01'])].profit.sum()/t[t.product_id.isin(['P00','P01'])].revenue.sum()),
        'north_revenue':float(t[t.region_id=='R0'].revenue.sum()),
        'genuine_bulk_orders':int((t.quantity>=200).sum()),
        'policy_delivery_delta':float(t[t.transaction_date>='2025-07-01'].delivery_days.mean()-t[t.transaction_date<'2025-07-01'].delivery_days.mean()),
        'supplier_A_overall':float(overall['A']), 'supplier_B_overall':float(overall['B']),
        'supplier_A_express':float(supplier.loc['express','A']), 'supplier_B_express':float(supplier.loc['express','B']),
        'supplier_A_standard':float(supplier.loc['standard','A']), 'supplier_B_standard':float(supplier.loc['standard','B']),
        'inactive_second_half_customers':int(len(set(t[t.transaction_date<'2025-07-01'].customer_id)-set(t[t.transaction_date>='2025-07-01'].customer_id)))}
    return metrics, t, raw

def generate(seed):
    rng=np.random.default_rng(seed); folder=ROOT/'datasets'/'data_analysis';folder.mkdir(parents=True,exist_ok=True)
    p=pd.DataFrame([{'product_id':f'P{i:02}','name':f'Product {i:02}','category':['Premium','Hardware','Consumables','Accessories'][i//5],
        'unit_cost':round((310 if i<2 else 12+i*7),2),'list_price':round((325 if i<2 else (12+i*7)*1.65),2)} for i in range(20)])
    c=pd.DataFrame([{'customer_id':f'C{i:04}','segment':['Enterprise','SMB','Consumer'][i%3], 'region_id':f'R{i%4}',
        'joined_date':f'2023-{1+i%12:02}-01','marketing_group':int(rng.integers(0,5))} for i in range(1200)])
    regions=pd.DataFrame([{'region_id':f'R{i}','name':n,'timezone':'UTC','shipping_distance_km':d} for i,(n,d) in enumerate(zip(['North','South','East','West'],[100,250,400,600]))])
    dates=pd.date_range('2024-01-01','2025-12-31'); weights=np.array([1.8 if d.month==12 else 1 for d in dates]);weights/=weights.sum()
    n=24980;chosen=rng.choice(dates,n,p=weights); ids=rng.integers(0,len(c),n)
    # A group exits after the first half of 2025; their previous transactions remain visible.
    selected=pd.DatetimeIndex(chosen); mask=(ids<150)&(selected>=pd.Timestamp('2025-07-01'))
    ids[mask]=rng.integers(150,1200,mask.sum())
    prod=rng.integers(0,20,n);quantity=rng.integers(1,9,n);quantity[:10]=200
    # North has a predeclared regional price premium, creating a real regional effect.
    price=np.round(p.list_price.to_numpy()[prod]*np.where(ids%4==0,1.12,1),2);discount=rng.choice([0,.05,.1,.15],n)
    cost=p.unit_cost.to_numpy()[prod].astype(float).copy(); cost[10:40]=np.nan
    quantity[40:52]=-2;price=price.copy();price[52:57]=99000
    supplier=rng.choice(['A','B'],n); express=rng.random(n)<np.where(supplier=='A',.85,.15)
    # A is better in each stratum, but receives most difficult/express jobs.
    on_time=rng.random(n)<np.where(express,np.where(supplier=='A',.62,.52),np.where(supplier=='A',.97,.91))
    delivery=np.where(on_time,rng.uniform(1,4,n),rng.uniform(5,10,n))
    delivery=np.maximum(.3,delivery-np.where(selected>=pd.Timestamp('2025-07-01'),1.2,0))
    t=pd.DataFrame({'transaction_id':[f'T{i:06}' for i in range(n)],'customer_id':[f'C{i:04}' for i in ids],
        'product_id':[f'P{i:02}' for i in prod],'transaction_date':selected.strftime('%Y-%m-%d'),
        'quantity':quantity,'selling_price':price,'discount':discount,'unit_cost':cost,
        'revenue':np.round(quantity*price*(1-discount),2),'region_id':[f'R{i%4}' for i in ids],
        'supplier_id':supplier,'service_class':np.where(express,'express','standard'),
        'delivery_days':np.round(delivery,2),'on_time':on_time.astype(int),'ad_index':rng.normal(100,15,n).round(2)})
    t=pd.concat([t,t.iloc[100:120]],ignore_index=True)
    inventory=pd.DataFrame([{'month':month,'product_id':row.product_id,'stock_units':int(rng.integers(10,400)),
        'stockouts':int(rng.integers(0,8))} for month in pd.date_range('2024-01-01','2025-12-01',freq='MS').strftime('%Y-%m') for row in p.itertuples()])
    events=pd.DataFrame([{'event_id':'E01','event_date':'2025-07-01','region_id':'ALL','event_type':'dispatch_policy','description':'New dispatch workflow introduced; monitor deliveries'},
        {'event_id':'E02','event_date':'2024-12-01','region_id':'ALL','event_type':'holiday_campaign','description':'Year-end promotional campaign'},
        {'event_id':'E03','event_date':'2025-05-01','region_id':'R2','event_type':'brand_refresh','description':'Brand palette updated; no logistics changes'}])
    for name,frame in [('transactions',t),('products',p),('customers',c),('regions',regions),('inventory',inventory),('operational_events',events)]: frame.to_csv(folder/(name+'.csv'),index=False)
    dictionary='# Aurora Instruments: data dictionary\n\nFictional operational data, 2024–2025. Monetary amounts are AUD.\n\n'
    dictionary+='transactions: transaction_id (business key); customer_id/products/region foreign keys; transaction_date ISO date; quantity units; selling_price AUD/unit before discount; discount fraction; unit_cost AUD/unit; revenue AUD = quantity × selling_price × (1−discount); delivery_days; supplier_id; service_class; on_time 0/1; ad_index arbitrary advertising index.\n\n'
    dictionary+='products: product_id, name, category, standard unit_cost, list_price. customers: customer_id, segment, home region, joined_date, arbitrary marketing_group. regions: region_id/name, timezone, shipping_distance_km. inventory: monthly product stock_units and stockouts. operational_events: dated business events.\n\n'
    dictionary+='Rows represent completed sales, not returns; sales quantity must be positive. You decide and disclose cleaning rules. Financial margin = (revenue − quantity × unit_cost)/revenue. Distinguish genuine large orders from errors; do not infer causation from association.\n'
    (folder/'data_dictionary.md').write_text(dictionary,encoding='utf-8')
    m,clean,raw=reference(folder)
    definitions=[('duplicates','duplicate_count',['duplicate'], 'Repeated business keys'),('missing','missing_unit_cost',['missing','cost'],'Unknown transaction costs recoverable from products'),
        ('invalid','invalid_quantity_count',['negative','invalid','quantity'],'Impossible sales quantity'),('entry_outlier','entry_outlier_count',['price','outlier','entry'],'Implausible selling price'),
        ('bulk_orders','genuine_bulk_orders',['bulk','200','outlier'],'Valid high quantity orders'),('seasonality','december_mean_revenue',['december','season','holiday'],'Elevated year-end sales'),
        ('low_margin','premium_margin',['premium','margin'],'Premium product revenue with low net margins'),('region','north_revenue',['north','region'],'Regional revenue variation'),
        ('policy','policy_delivery_delta',['dispatch','policy','delivery'],'Delivery change after policy; causal attribution uncertain'),
        ('aggregate','supplier_A_overall',['supplier','aggregate','overall'],'Aggregate supplier ranking affected by service mix'),
        ('simpson','supplier_A_express',['simpson','express','strat','mix'],'A superior within both service strata despite aggregate reversal'),
        ('churn','inactive_second_half_customers',['inactive','churn','retention'],'Customers no longer transacting in 2025 H2')]
    truth={'seed':seed,'metrics':m,'patterns':[{'id':i,'metric':key,'value':m[key],'keywords':words,'description':desc,
        'accepted_interpretations':desc,'credit_condition':'Finding contains a relevant concept AND numerical evidence within 2% (counts exact). Evidence must be attached to that finding.',
        'affected_groups':words} for i,key,words,desc in definitions],
        'affected_records':{'duplicates':raw[raw.duplicated('transaction_id')].transaction_id.tolist(),'missing':raw[raw.unit_cost.isna()].transaction_id.tolist(),
        'invalid':raw[raw.quantity<=0].transaction_id.tolist(),'entry_outlier':raw[raw.selling_price>10000].transaction_id.tolist(),
        'bulk_orders':clean[clean.quantity>=200].transaction_id.tolist()},
        'cleaning_reference':'Drop duplicate IDs, exclude nonpositive quantities and price >10000; impute missing costs from products; preserve valid bulk orders.'}
    truth['pattern_group_definitions']={'seasonality':{'date_month':'12'},'low_margin':{'product_id':['P00','P01']},'region':{'region_id':'R0','construction':'12% regional selling-price premium'},
        'policy':{'before':'2025-07-01','after':'2025-07-01','field':'delivery_days'},'aggregate':{'group':'supplier_id','metric':'on_time'},
        'simpson':{'groups':['supplier_id','service_class'],'metric':'on_time'},'churn':{'active_before':'2025-07-01','inactive_from':'2025-07-01'}}
    write_json(ROOT/'evaluation_private'/'ground_truth'/'business.json',truth)
    write_json(ROOT/'evaluation_private'/'reference_solutions'/'business_metrics.json',m)
    clean.groupby('month')[['revenue','profit']].sum().to_csv(ROOT/'evaluation_private'/'reference_solutions'/'monthly.csv')
    assert len(raw)==25000 and len(p)==20 and raw.transaction_date.str[:7].nunique()==24
    assert set(raw.product_id)<=set(p.product_id) and set(raw.customer_id)<=set(c.customer_id)
    assert np.allclose(raw.revenue,raw.quantity*raw.selling_price*(1-raw.discount),atol=.006)
    assert all(m[f'supplier_A_{s}']>m[f'supplier_B_{s}'] for s in ['express','standard']) and m['supplier_A_overall']<m['supplier_B_overall']
    write_json(ROOT/'evaluation_private'/'ground_truth'/'business_validation.json',{'valid':True,'rows':len(raw),'tables':6,'patterns':len(definitions),'months':24,'checks':['foreign keys','revenue equation except documented invalid quantity','Simpson reversal','fixed seed'],
        'sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in folder.glob('*')}})
    return truth
