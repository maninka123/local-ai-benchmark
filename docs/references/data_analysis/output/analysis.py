"""Aurora Instruments reference analysis. Python 3 + pandas, numpy, matplotlib, Pillow.
Run: D:/LocalLLM/benchmark-env/Scripts/python.exe path/to/output/analysis.py
Optional --data-dir overrides the original datasets/data_analysis location.
Only reads the six supplied CSVs and dictionary; all writes stay beside this script.
"""
from pathlib import Path
import argparse, hashlib, json, sys, platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
parser=argparse.ArgumentParser()
parser.add_argument('--data-dir',type=Path,default=ROOT/'datasets/data_analysis')
args=parser.parse_args()
D=args.data_dir.resolve()
(OUT/'figures').mkdir(exist_ok=True)
(OUT/'tables').mkdir(exist_ok=True)
def dump(name,value):
 (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf-8')
def records(df):
 return json.loads(df.reset_index().to_json(orient='records'))
def aggregate(df,by):
 g=df.groupby(by,observed=True).agg(transactions=('revenue','size'),revenue=('revenue','sum'),cost=('cost','sum'),gross_profit=('gross_profit','sum'),units=('quantity','sum'),on_time_count=('on_time','sum'),mean_delivery_days=('delivery_days','mean'))
 g['margin']=g.gross_profit/g.revenue
 g['on_time_rate']=g.on_time_count/g.transactions
 return g

names=['transactions','products','customers','regions','inventory','operational_events']
tables={n:pd.read_csv(D/f'{n}.csv') for n in names}
keys={'transactions':['transaction_id'],'products':['product_id'],'customers':['customer_id'],'regions':['region_id'],'inventory':['month','product_id'],'operational_events':['event_id']}
profile={}
for name,df in tables.items():
 profile[name]={'rows':len(df),'columns':len(df.columns),'dtypes':{c:str(v) for c,v in df.dtypes.items()},'missing':{c:int(v) for c,v in df.isna().sum().items()},'exact_duplicate_rows':int(df.duplicated().sum()),'duplicate_key_rows':int(df.duplicated(keys[name]).sum()),'key':keys[name]}
 if name!='transactions': assert not df.duplicated(keys[name]).any()
date_checks={}
for table,col,fmt in [('transactions','transaction_date','%Y-%m-%d'),('customers','joined_date','%Y-%m-%d'),('inventory','month','%Y-%m'),('operational_events','event_date','%Y-%m-%d')]:
 parsed=pd.to_datetime(tables[table][col],format=fmt,errors='coerce')
 date_checks[f'{table}.{col}']={'invalid':int(parsed.isna().sum()),'min':str(parsed.min().date()),'max':str(parsed.max().date())}
 assert parsed.notna().all()
 for key,value in date_checks[f'{table}.{col}'].items(): profile[table][f'{col}_{key}']=value
raw=tables['transactions']
dup=raw[raw.duplicated()].copy()
dedup=raw.drop_duplicates().copy()
assert not dedup.transaction_id.duplicated().any(), 'Conflicting business keys require resolution'
t=dedup.merge(tables['products'].rename(columns={'name':'product_name','unit_cost':'standard_cost'}),on='product_id',how='left',validate='many_to_one',indicator='_product_join')
t=t.merge(tables['customers'].rename(columns={'region_id':'home_region_id'}),on='customer_id',how='left',validate='many_to_one',indicator='_customer_join')
t=t.merge(tables['regions'].rename(columns={'name':'region_name'}),on='region_id',how='left',validate='many_to_one',indicator='_region_join')
join_audit={c:int((t[c]!='both').sum()) for c in ['_product_join','_customer_join','_region_join']}
assert len(t)==len(dedup) and not any(join_audit.values())
assert tables['inventory'].product_id.isin(tables['products'].product_id).all()
assert tables['customers'].region_id.isin(tables['regions'].region_id).all()
assert tables['operational_events'].region_id.isin([*tables['regions'].region_id,'ALL']).all()
assert (tables['products'][['unit_cost','list_price']]>0).all().all()
assert (tables['regions'].shipping_distance_km>=0).all()
assert (tables['inventory'][['stock_units','stockouts']]>=0).all().all()
assert (pd.to_datetime(t.transaction_date)>=pd.to_datetime(t.joined_date)).all()
t['price_to_list']=t.selling_price/t.list_price
t['invalid_quantity']=t.quantity<=0
t['price_quarantine']=t.price_to_list>10
assert (t.selling_price>0).all() and t.discount.between(0,1).all()
assert t.on_time.isin([0,1]).all() and (t.delivery_days>=0).all()
assert t.unit_cost.dropna().ge(0).all() and t.ad_index.ge(0).all()
assert np.isfinite(t.select_dtypes('number').drop(columns=['unit_cost'])).all().all()
delta=t.revenue-t.quantity*t.selling_price*(1-t.discount)
assert delta.abs().max()<=.011
assert ((t.unit_cost==t.standard_cost)|t.unit_cost.isna()).all()
t['imputed_cost']=t.unit_cost.isna()
t['effective_unit_cost']=t.unit_cost.fillna(t.standard_cost)
t['cost']=t.quantity*t.effective_unit_cost
t['gross_profit']=t.revenue-t.cost
t['year']=t.transaction_date.str[:4]
t['month']=t.transaction_date.str[:7]
t['period']=np.where(t.transaction_date<'2025-07-01','Before July 2025','July–December 2025')
q=t[t.invalid_quantity|t.price_quarantine].copy()
q['quarantine_reason']=np.where(q.invalid_quantity,'nonpositive quantity in completed sales','unit price exceeds 10x product list price')
q.to_csv(OUT/'tables/quarantined_transactions.csv',index=False)
dup.to_csv(OUT/'tables/exact_duplicate_copies.csv',index=False)
t=t[~t.invalid_quantity & ~t.price_quarantine].copy()
assert len(t)==24963
t[t.imputed_cost].to_csv(OUT/'tables/imputed_cost_rows.csv',index=False)
t[t.quantity>8].to_csv(OUT/'tables/retained_large_orders.csv',index=False)
groups={name:aggregate(t,by) for name,by in {'annual':'year','monthly':'month','category':'category','product':'product_id','region':'region_name','segment':'segment','supplier':'supplier_id','service':'service_class','supplier_service':['supplier_id','service_class'],'period':'period','period_region':['period','region_name'],'period_service':['period','service_class'],'customer':'customer_id'}.items()}
for name,g in groups.items():
 g.to_csv(OUT/f'tables/{name}.csv')
 assert abs(g.revenue.sum()-t.revenue.sum())<1e-6
 assert abs(g.gross_profit.sum()-t.gross_profit.sum())<1e-6
inv=tables['inventory']
pm=aggregate(t,['month','product_id']).reset_index().merge(inv,on=['month','product_id'],how='outer',validate='one_to_one',indicator=True)
assert len(pm)==480 and pm._merge.eq('both').all()
assert len(set(inv.month))==24 and inv.groupby('month').size().eq(20).all()
pm.to_csv(OUT/'tables/product_month_inventory_sales.csv',index=False)
large=t[t.quantity>8]
no_large=t[t.quantity<=8]
supplier=groups['supplier_service']
weights=t.service_class.value_counts(normalize=True).to_dict()
std_rates={s:sum(supplier.loc[(s,c),'on_time_rate']*w for c,w in weights.items()) for s in ['A','B']}
customer=groups['customer'].sort_values('revenue',ascending=False)
annual=groups['annual']; monthly=groups['monthly']; period=groups['period']
period2025=aggregate(t[t.year=='2025'],'period')
seasonal={y:{'december_revenue':monthly.loc[f'{y}-12','revenue'],'jan_nov_mean_revenue':monthly.loc[[f'{y}-{m:02d}' for m in range(1,12)],'revenue'].mean(),'december_transactions':monthly.loc[f'{y}-12','transactions'],'jan_nov_mean_transactions':monthly.loc[[f'{y}-{m:02d}' for m in range(1,12)],'transactions'].mean()} for y in ['2024','2025']}
for v in seasonal.values(): v['december_uplift']=v['december_revenue']/v['jan_nov_mean_revenue']-1
premium=t[t.product_id.isin(['P00','P01'])]
north=t[t.region_id=='R0'];other=t[t.region_id!='R0']
counterfactual=(north.revenue/1.12-north.cost).sum()/(north.revenue/1.12).sum()
cost_known=t[~t.imputed_cost]
metrics={
 'totals':{'transactions':len(t),'customers':t.customer_id.nunique(),'revenue':t.revenue.sum(),'cost':t.cost.sum(),'gross_profit':t.gross_profit.sum(),'margin':t.gross_profit.sum()/t.revenue.sum(),'units':t.quantity.sum(),'on_time_rate':t.on_time.mean()},
 'cleaning':{'raw_rows':len(raw),'raw_revenue':raw.revenue.sum(),'duplicate_copies':len(dup),'duplicate_revenue':dup.revenue.sum(),'dedup_revenue':dedup.revenue.sum(),'invalid_quantity_rows':int(q.invalid_quantity.sum()),'invalid_quantity_revenue':q.loc[q.invalid_quantity,'revenue'].sum(),'extreme_price_rows':int(q.price_quarantine.sum()),'extreme_price_revenue':q.loc[q.price_quarantine,'revenue'].sum(),'min_extreme_price_to_list':q.loc[q.price_quarantine,'price_to_list'].min(),'max_extreme_price_to_list':q.loc[q.price_quarantine,'price_to_list'].max(),'missing_cost_rows':int(t.imputed_cost.sum()),'imputed_cost':t.loc[t.imputed_cost,'cost'].sum(),'imputed_rows_revenue':t.loc[t.imputed_cost,'revenue'].sum(),'known_cost_margin':cost_known.gross_profit.sum()/cost_known.revenue.sum(),'revenue_formula_max_error':delta.abs().max(),'home_region_disagreements':int((t.region_id!=t.home_region_id).sum())},
 'year_over_year':{'revenue_change':annual.loc['2025','revenue']/annual.loc['2024','revenue']-1,'profit_change':annual.loc['2025','gross_profit']/annual.loc['2024','gross_profit']-1,'transactions_change':annual.loc['2025','transactions']/annual.loc['2024','transactions']-1,'units_change':annual.loc['2025','units']/annual.loc['2024','units']-1,'without_large_orders_revenue_change':no_large[no_large.year=='2025'].revenue.sum()/no_large[no_large.year=='2024'].revenue.sum()-1},
 'seasonal':seasonal,
 'premium_pair':{'transactions':len(premium),'revenue':premium.revenue.sum(),'gross_profit':premium.gross_profit.sum(),'margin':premium.gross_profit.sum()/premium.revenue.sum(),'revenue_share':premium.revenue.sum()/t.revenue.sum(),'loss_making_transactions':int(premium.gross_profit.lt(0).sum()),'all_loss_making_transactions':int(t.gross_profit.lt(0).sum()),'catalog_break_even_discount':1-310/325},
 'region_pricing':{'north_mean_price_to_list':north.price_to_list.mean(),'other_mean_price_to_list':other.price_to_list.mean(),'north_discount':north.discount.mean(),'other_discount':other.discount.mean(),'north_margin_without_12pct_price_premium_scenario':counterfactual},
 'supplier':{'common_service_weights':weights,'standardized_on_time_rates':std_rates,'express_shares':{s:float((t[t.supplier_id==s].service_class=='express').mean()) for s in ['A','B']}},
 'delivery':{'2025_half_year':records(period2025),'pre_post_mean_difference':period.loc['July–December 2025','mean_delivery_days']-period.loc['Before July 2025','mean_delivery_days'],'pre_post_on_time_difference':period.loc['July–December 2025','on_time_rate']-period.loc['Before July 2025','on_time_rate']},
 'customer':{'top10_revenue_share':customer.head(10).revenue.sum()/t.revenue.sum(),'top120_revenue_share':customer.head(120).revenue.sum()/t.revenue.sum(),'largest_customer':customer.index[0],'largest_customer_share':customer.iloc[0].revenue/t.revenue.sum(),'negative_profit_customers':int(customer.gross_profit.lt(0).sum())},
 'large_orders':{'rows':len(large),'revenue':large.revenue.sum(),'revenue_share':large.revenue.sum()/t.revenue.sum(),'gross_profit':large.gross_profit.sum()},
 'inventory':{'product_months':len(pm),'stockout_count':int(inv.stockouts.sum()),'positive_stockout_months':int(inv.stockouts.gt(0).sum()),'units_stockouts_pearson':pm.units.corr(pm.stockouts),'stock_stockouts_pearson':pm.stock_units.corr(pm.stockouts)},
 'advertising':{'transaction_ad_revenue_pearson':t.ad_index.corr(t.revenue)},
 'groups':{name:records(g) for name,g in groups.items() if name!='customer'},
 'events':tables['operational_events'].to_dict(orient='records')
}
dump('metrics.json',metrics)
dump('data_profile.json',profile)
dump('source_manifest.json',{'scope':'Only datasets/data_analysis; no external sources','files':[{'path':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(D.iterdir()) if p.name in [f'{n}.csv' for n in names]+['data_dictionary.md']], 'environment':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__},'join_checks':join_audit,'inventory_join_unmatched':0,'all_financial_subtotals_reconciled':True})

plt.rcParams.update({'figure.facecolor':'#ffffff','axes.facecolor':'#ffffff','axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#d8e1eb','axes.labelcolor':'#40536b','text.color':'#172b46','xtick.color':'#40536b','ytick.color':'#40536b','font.family':'DejaVu Sans','font.size':10,'axes.titleweight':'bold','axes.titlesize':14,'grid.color':'#e9eef5','axes.axisbelow':True,'savefig.facecolor':'white'})
BLUE='#1769aa'; TEAL='#009b88'; ORANGE='#d87524'; RED='#c64c5b'
def save(fig,i):
 fig.tight_layout(pad=2)
 fig.savefig(OUT/f'figures/figure_{i:02d}.png',dpi=165,bbox_inches='tight')
 plt.close(fig)
def moneyaxis(ax):ax.yaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x/1e6:.1f}m'))

fig,ax=plt.subplots(figsize=(10.5,4.4))
x=np.arange(24);ax.plot(x,monthly.revenue,marker='o',color=BLUE,label='Net sales revenue')
ax.plot(x,monthly.gross_profit,marker='s',color=TEAL,label='Gross profit')
for i in [11,23]:ax.scatter(i,monthly.iloc[i].revenue,s=95,color=ORANGE,zorder=5)
ax.set(ylim=(0,1400000),ylabel='AUD millions',title='December sales peaks conceal a 1.9% annual revenue decline')
ax.set_xticks(x[::2],monthly.index[::2],rotation=35,ha='right');moneyaxis(ax);ax.grid(axis='y');ax.legend(frameon=False,loc='upper left');save(fig,1)

fig,axs=plt.subplots(1,2,figsize=(10.5,4.5),gridspec_kw={'width_ratios':[1,1.05]})
cat=groups['category'].sort_values('margin')
axs[0].barh(cat.index,cat.margin,color=[ORANGE,BLUE,BLUE,BLUE]);axs[0].set(xlim=(0,.43),title='Premium margins lag\nother categories',xlabel='Gross margin (%)');axs[0].set_xticks([0,.1,.2,.3,.4]);axs[0].xaxis.set_major_formatter(PercentFormatter(1));axs[0].grid(axis='x')
for i,v in enumerate(cat.margin):axs[0].text(v+.007,i,f'{v:.1%}',va='center')
pr=groups['product'].loc[['P00','P01']];axs[1].bar(pr.index,pr.gross_profit,color=[TEAL,RED]);axs[1].axhline(0,color='#50647c',lw=.8);axs[1].set(title='P00 and P01 generate almost no profit',ylabel='Gross profit (AUD)',ylim=(-15000,9000));axs[1].grid(axis='y')
for i,v in enumerate(pr.gross_profit):axs[1].text(i,v+(450 if v>0 else -450),f'${v:,.0f}',ha='center',va='bottom' if v>0 else 'top')
save(fig,2)

fig,axs=plt.subplots(1,2,figsize=(10.5,4.4))
reg=groups['region'].loc[['North','South','East','West']]
axs[0].bar(reg.index,reg.revenue/1e6,color=[ORANGE,BLUE,BLUE,BLUE]);axs[0].set(title='North leads on sales',ylabel='Revenue (AUD millions)',ylim=(0,5.5));axs[0].grid(axis='y')
axs[1].bar(reg.index,reg.margin,color=[ORANGE,BLUE,BLUE,BLUE]);axs[1].set(title='A systematic price premium lifts margin',ylabel='Gross margin (%)',ylim=(0,.40));axs[1].yaxis.set_major_formatter(PercentFormatter(1));axs[1].grid(axis='y')
for i,v in enumerate(reg.margin):axs[1].text(i,v+.008,f'{v:.1%}',ha='center')
save(fig,3)

fig,ax=plt.subplots(figsize=(10.5,4.5))
labels=['All orders\n(observed mix)','Express only','Standard only','Same service mix\n(standardized)'];pos=np.arange(4);w=.34
for j,s in enumerate(['A','B']):
 vals=[groups['supplier'].loc[s,'on_time_rate'],supplier.loc[(s,'express'),'on_time_rate'],supplier.loc[(s,'standard'),'on_time_rate'],std_rates[s]]
 bars=ax.bar(pos+(j-.5)*w,vals,w,label=f'Supplier {s}',color=BLUE if s=='A' else TEAL)
 for b,v in zip(bars,vals):ax.text(b.get_x()+w/2,v+.016,f'{v:.1%}',ha='center',fontsize=10)
ax.set_xticks(pos,labels);ax.set(ylim=(0,1.13),ylabel='On-time deliveries (%)',title='Supplier ranking reverses when service mix is held comparable');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y');ax.legend(loc='upper left',frameon=False,ncol=2);save(fig,4)

fig,axs=plt.subplots(2,1,figsize=(10.5,6.5),sharex=True)
axs[0].plot(x,monthly.mean_delivery_days,color=BLUE,marker='o');axs[0].set(ylim=(0,4.5),ylabel='Mean delivery days',title='Delivery times fall after July 2025; on-time rates remain similar')
axs[1].plot(x,monthly.on_time_rate,color=TEAL,marker='s');axs[1].set(ylim=(0,1),ylabel='On-time deliveries (%)');axs[1].yaxis.set_major_formatter(PercentFormatter(1))
for ax in axs:ax.axvline(17.5,color=ORANGE,ls='--',label='Dispatch policy: 1 July 2025');ax.grid(axis='y')
axs[0].legend(loc='lower left',frameon=False);axs[1].set_xticks(x[::2],monthly.index[::2],rotation=35,ha='right');save(fig,5)

fig,axs=plt.subplots(1,2,figsize=(10.5,4.5))
cumulative=customer.revenue.cumsum()/customer.revenue.sum()
axs[0].plot(np.arange(1,len(customer)+1)/len(customer),cumulative,color=BLUE,lw=2);axs[0].plot([0,1],[0,1],ls='--',color='#8b9aae',label='Equal revenue per customer');axs[0].scatter(.1,cumulative.iloc[119],color=ORANGE,zorder=5);axs[0].set(xlim=(0,1),ylim=(0,1),title='Top 10% of customers generate\n17.1% of revenue',xlabel='Customers, ranked by revenue (%)',ylabel='Cumulative revenue (%)');axs[0].xaxis.set_major_formatter(PercentFormatter(1));axs[0].yaxis.set_major_formatter(PercentFormatter(1));axs[0].legend(frameon=False,fontsize=8);axs[0].grid()
seg=groups['segment'];axs[1].bar(seg.index,seg.revenue/1e6,color=[BLUE,TEAL,ORANGE]);axs[1].set(ylim=(0,7),title='Sales are spread across\nall three segments',ylabel='Revenue (AUD millions)');axs[1].grid(axis='y');save(fig,6)

fig,axs=plt.subplots(1,2,figsize=(10.5,4.5))
preprice=dedup.merge(tables['products'][['product_id','list_price']],on='product_id',validate='many_to_one');valid=preprice[preprice.quantity>0]
normal=valid.selling_price/valid.list_price<=10
axs[0].scatter(valid.loc[normal,'quantity'],valid.loc[normal,'selling_price']/valid.loc[normal,'list_price'],alpha=.16,s=12,color=BLUE,label='Retained rows');axs[0].scatter(valid.loc[~normal,'quantity'],valid.loc[~normal,'selling_price']/valid.loc[~normal,'list_price'],s=60,color=RED,marker='x',label='Quarantined prices');axs[0].set_yscale('log');axs[0].set(xlim=(0,210),xlabel='Quantity (units)',ylabel='Unit price / catalog list price (log scale)',title='Large orders differ from\nextreme unit-price anomalies');axs[0].legend(frameon=False,fontsize=8)
amounts=[raw.revenue.sum(),dedup.revenue.sum(),dedup[dedup.quantity>0].revenue.sum(),t.revenue.sum()];axs[1].bar(['Raw','Deduplicated','Positive\nquantities','Price-screened\nprimary'],np.array(amounts)/1e6,color=['#9cb0c6','#7595b6','#497caa',TEAL]);axs[1].set(ylim=(0,22),ylabel='Revenue (AUD millions)',title='Cleaning changes the financial baseline');axs[1].grid(axis='y')
for i,v in enumerate(amounts):axs[1].text(i,v/1e6+.35,f'{v/1e6:.2f}m',ha='center')
save(fig,7)

fig,axs=plt.subplots(1,2,figsize=(10.5,4.5))
axs[0].scatter(pm.stockouts,pm.units,color=BLUE,alpha=.35,s=22);axs[0].set(title=f"Stockouts and sold units: r = {pm.stockouts.corr(pm.units):.3f}",xlabel='Recorded stockouts per product-month',ylabel='Sold units per product-month',xlim=(-.5,7.5),ylim=(0,600));axs[0].grid(axis='y')
annualinv=inv.assign(year=inv.month.str[:4]).groupby('year').stockouts.sum();axs[1].bar(annualinv.index,annualinv.values,color=[BLUE,TEAL]);axs[1].set(title='Recorded stockouts fell modestly',ylabel='Sum of product-month stockout counts',ylim=(0,950));axs[1].grid(axis='y')
for i,v in enumerate(annualinv):axs[1].text(i,v+15,str(v),ha='center')
save(fig,8)
print(json.dumps({k:v for k,v in metrics.items() if k not in ['groups','events']},indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
