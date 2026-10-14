exec((__import__('pathlib').Path(__file__).parent/'explore.py').read_text().split('for name,df')[0])
t=tables['transactions'].drop_duplicates().copy()
t=t.merge(tables['products'].rename(columns={'unit_cost':'standard_cost','name':'product_name'}),on='product_id',validate='many_to_one')
print('Price ratio frequencies', (t.selling_price/t.list_price).round(4).value_counts().to_string())
print('high price',t[t.selling_price/t.list_price>2].to_string(index=False))
print('cost differences',t[(t.unit_cost.notna())&(t.unit_cost!=t.standard_cost)].shape)
print('max quantity frequencies',t.quantity.value_counts().sort_index().to_string())
print('large orders',t[t.quantity>50].to_string(index=False))
t=t[(t.quantity>0)&(t.selling_price/t.list_price<10)].copy()
t.unit_cost=t.unit_cost.fillna(t.standard_cost)
t['cost']=t.quantity*t.unit_cost;t['profit']=t.revenue-t.cost
t['month']=t.transaction_date.str[:7]; t['year']=t.transaction_date.str[:4];t['post']=t.transaction_date>='2025-07-01'
t=t.merge(tables['customers'].rename(columns={'region_id':'home_region_id'}),on='customer_id',validate='many_to_one')
for groups in ['year','month','category','product_id','region_id','segment','supplier_id','service_class',['supplier_id','service_class'],'post',['post','region_id'],['post','service_class']]:
 g=t.groupby(groups).agg(n=('revenue','size'),revenue=('revenue','sum'),profit=('profit','sum'),units=('quantity','sum'),on_time=('on_time','mean'),days=('delivery_days','mean'));g['margin']=g.profit/g.revenue
 print('\nGROUP',groups,'\n',g.to_string())
print('corr ad/rev',t[['ad_index','revenue']].corr())
print('delivery correlations', t[['delivery_days','quantity','revenue','ad_index']].corr())
print('home differs',sum(t.home_region_id!=t.region_id))
c=t.groupby('customer_id').agg(revenue=('revenue','sum'),n=('revenue','size'),profit=('profit','sum')).sort_values('revenue',ascending=False)
print('customers',c.head(15).to_string());print('top shares', {k:c.head(k).revenue.sum()/c.revenue.sum() for k in [1,10,60,120]})
inv=tables['inventory'];pm=t.groupby(['month','product_id']).agg(revenue=('revenue','sum'),units=('quantity','sum')).reset_index().merge(inv,on=['month','product_id'],validate='one_to_one')
print('inventory correlation',pm[['stock_units','stockouts','units','revenue']].corr().to_string());print('inv annual',inv.assign(year=inv.month.str[:4]).groupby('year')[['stock_units','stockouts']].agg(['sum','mean']).to_string())
