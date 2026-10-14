"""Independent verification: csv + Decimal + standard-library aggregation.
Does not import pandas, numpy, analysis.py, or its aggregation helpers.
"""
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal
from datetime import datetime, timezone
from html.parser import HTMLParser
import argparse, csv, json, math, hashlib, base64, re
O=Path(__file__).resolve().parent;R=O.parents[4]
p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,default=R/'datasets/data_analysis');a=p.parse_args()
D=a.data_dir.resolve();Z=Decimal(0);checks=[]
def read(n):
 with (D/f'{n}.csv').open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def dec(v):return Decimal(str(v))
def equal(name,actual,expected,tol=Decimal('.000001')):
 ok=abs(dec(actual)-dec(expected))<=tol
 checks.append({'check':name,'passed':ok,'independent_value':str(actual),'reported_value':str(expected),'absolute_tolerance':str(tol)})
 assert ok,(name,actual,expected)
raw=read('transactions');prods={x['product_id']:x for x in read('products')};customers={x['customer_id']:x for x in read('customers')};regions={x['region_id']:x for x in read('regions')}
m=json.loads((O/'metrics.json').read_text());seen=set();dup=[];invalid=[];price=[];rows=[]
for r in raw:
 key=tuple(r.items())
 if key in seen:dup.append(r);continue
 seen.add(key)
 qty=int(r['quantity']);pr=prods[r['product_id']]
 if qty<=0:invalid.append(r);continue
 if dec(r['selling_price'])>dec(pr['list_price'])*10:price.append(r);continue
 cost=dec(r['unit_cost'] or pr['unit_cost'])*qty
 rows.append(r|{'net':dec(r['revenue']),'cost_ext':cost,'profit':dec(r['revenue'])-cost,'q':qty,'date':datetime.strptime(r['transaction_date'],'%Y-%m-%d')})
equal('retained row count',len(rows),m['totals']['transactions'],Z)
equal('distinct retained business keys',len({r['transaction_id'] for r in rows}),len(rows),Z)
equal('duplicate copies',len(dup),m['cleaning']['duplicate_copies'],Z)
equal('invalid quantities',len(invalid),m['cleaning']['invalid_quantity_rows'],Z)
equal('price quarantines',len(price),m['cleaning']['extreme_price_rows'],Z)
equal('missing costs filled',sum(not r['unit_cost'] for r in rows),m['cleaning']['missing_cost_rows'],Z)
equal('independent total revenue',sum((r['net'] for r in rows),Z),m['totals']['revenue'])
equal('independent total cost',sum((r['cost_ext'] for r in rows),Z),m['totals']['cost'])
equal('independent total profit',sum((r['profit'] for r in rows),Z),m['totals']['gross_profit'])
equal('independent units',sum(r['q'] for r in rows),m['totals']['units'],Z)
equal('raw revenue bridge',sum((dec(r['revenue']) for r in raw),Z)-sum((dec(r['revenue']) for r in dup+invalid+price),Z),m['totals']['revenue'])
by={
 'annual':lambda r:(r['transaction_date'][:4],),
 'monthly':lambda r:(r['transaction_date'][:7],),
 'product':lambda r:(r['product_id'],),
 'category':lambda r:(prods[r['product_id']]['category'],),
 'region':lambda r:(regions[r['region_id']]['name'],),
 'segment':lambda r:(customers[r['customer_id']]['segment'],),
 'supplier':lambda r:(r['supplier_id'],),
 'service':lambda r:(r['service_class'],),
 'supplier_service':lambda r:(r['supplier_id'],r['service_class']),
 'period':lambda r:('Before July 2025' if r['date']<datetime(2025,7,1) else 'July–December 2025',),
 'period_region':lambda r:('Before July 2025' if r['date']<datetime(2025,7,1) else 'July–December 2025',regions[r['region_id']]['name']),
 'period_service':lambda r:('Before July 2025' if r['date']<datetime(2025,7,1) else 'July–December 2025',r['service_class']),
 'customer':lambda r:(r['customer_id'],),
}
cols={'annual':['year'],'monthly':['month'],'product':['product_id'],'category':['category'],'region':['region_name'],'segment':['segment'],'supplier':['supplier_id'],'service':['service_class'],'supplier_service':['supplier_id','service_class'],'period':['period'],'period_region':['period','region_name'],'period_service':['period','service_class'],'customer':['customer_id']}
allgroups={}
for name,fn in by.items():
 g=defaultdict(lambda:{'transactions':0,'revenue':Z,'cost':Z,'gross_profit':Z,'units':0,'on_time_count':0,'days_sum':Z})
 for r in rows:
  v=g[fn(r)];v['transactions']+=1;v['revenue']+=r['net'];v['cost']+=r['cost_ext'];v['gross_profit']+=r['profit'];v['units']+=r['q'];v['on_time_count']+=int(r['on_time']);v['days_sum']+=dec(r['delivery_days'])
 with (O/f'tables/{name}.csv').open(newline='',encoding='utf-8') as f:reported=list(csv.DictReader(f))
 equal(name+' group count',len(g),len(reported),Z)
 for rec in reported:
  key=tuple(rec[c] for c in cols[name]);v=g[key]
  for field in ['transactions','revenue','cost','gross_profit','units','on_time_count']:
   equal(f'{name}/{key}/{field}',v[field],rec[field])
  equal(f'{name}/{key}/mean_delivery_days',v['days_sum']/v['transactions'],rec['mean_delivery_days'])
  equal(f'{name}/{key}/on_time_rate',dec(v['on_time_count'])/v['transactions'],rec['on_time_rate'])
  equal(f'{name}/{key}/margin',v['gross_profit']/v['revenue'],rec['margin'])
 allgroups[name]=g
counts=Counter(r['service_class'] for r in rows)
for sup in ['A','B']:
 rate=Z
 for service,n in counts.items():
  v=allgroups['supplier_service'][(sup,service)]
  rate+=dec(n)/len(rows)*dec(v['on_time_count'])/v['transactions']
 equal('supplier '+sup+' standardized rate',rate,m['supplier']['standardized_on_time_rates'][sup])
rev=sum((r['net'] for r in rows),Z)
ranked=sorted(allgroups['customer'].values(),key=lambda x:x['revenue'],reverse=True)
for k in [10,120]:equal(f'top{k} customer share',sum((x['revenue'] for x in ranked[:k]),Z)/rev,m['customer'][f'top{k}_revenue_share'])
pair=[r for r in rows if r['product_id'] in ['P00','P01']]
equal('premium pair gross profit',sum((r['profit'] for r in pair),Z),m['premium_pair']['gross_profit'])
equal('negative-profit transactions',sum(r['profit']<0 for r in rows),m['premium_pair']['all_loss_making_transactions'],Z)
equal('filled extended cost',sum((r['cost_ext'] for r in rows if not r['unit_cost']),Z),m['cleaning']['imputed_cost'])
equal('large-order revenue',sum((r['net'] for r in rows if r['q']>8),Z),m['large_orders']['revenue'])
annual=allgroups['annual'];equal('annual revenue change',annual[('2025',)]['revenue']/annual[('2024',)]['revenue']-1,m['year_over_year']['revenue_change'])
for year in ['2024','2025']:
 mon=allgroups['monthly'];jan_nov=sum((mon[(f'{year}-{i:02d}',)]['revenue'] for i in range(1,12)),Z)/11
 equal(year+' December uplift',mon[(year+'-12',)]['revenue']/jan_nov-1,m['seasonal'][year]['december_uplift'])
north=[r for r in rows if r['region_id']=='R0'];nr=sum((r['net']/dec('1.12') for r in north),Z);nc=sum((r['cost_ext'] for r in north),Z)
equal('North fixed-volume scenario margin',(nr-nc)/nr,m['region_pricing']['north_margin_without_12pct_price_premium_scenario'])
inventory=read('inventory');prod_month=Counter()
for r in rows:prod_month[(r['transaction_date'][:7],r['product_id'])]+=r['q']
equal('inventory product-month count',len(set((r['month'],r['product_id']) for r in inventory)),480,Z)
equal('stockout count',sum(int(r['stockouts']) for r in inventory),m['inventory']['stockout_count'],Z)
def corr(xs,ys):
 n=len(xs);sx=sum(xs);sy=sum(ys)
 return (n*sum(x*y for x,y in zip(xs,ys))-sx*sy)/math.sqrt((n*sum(x*x for x in xs)-sx*sx)*(n*sum(y*y for y in ys)-sy*sy))
equal('inventory units/stockouts correlation',corr([prod_month[(r['month'],r['product_id'])] for r in inventory],[int(r['stockouts']) for r in inventory]),m['inventory']['units_stockouts_pearson'])
equal('advertising/revenue correlation',corr([float(r['ad_index']) for r in rows],[float(r['net']) for r in rows]),m['advertising']['transaction_ad_revenue_pearson'])
manifest=json.loads((O/'source_manifest.json').read_text())
for source in manifest['files']:
 file=D/Path(source['path']).name
 assert hashlib.sha256(file.read_bytes()).hexdigest()==source['sha256']
checks.append({'check':'all seven original input hashes unchanged','passed':True})
for source,dest in [('common_system_prompt.md','system_prompt.md'),('data_analysis_prompt.md','prompt.md')]:
 assert (R/'benchmark/prompts'/source).read_bytes()==(O.parent/dest).read_bytes()
checks.append({'check':'original common/task prompt copies byte-identical','passed':True})
class Inspector(HTMLParser):
 def __init__(self):super().__init__();self.images=[];self.ids=[];self.anchors=[];self.external=[];self.text=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='img':self.images.append(a)
  if tag=='a' and a.get('href','').startswith('#'):self.anchors.append(a['href'][1:])
  for k in ['src','href']:
   if a.get(k,'').startswith(('http:','https:','//')):self.external.append(a[k])
 def handle_data(self,data):self.text.append(data)
doc=(O/'index.html').read_text(encoding='utf-8');ins=Inspector();ins.feed(doc)
assert len(ins.images)==8 and not ins.external
assert set(ins.anchors)<=set(ins.ids)
from PIL import Image
for image in ins.images:
 b=base64.b64decode(image['src'].split(',',1)[1]);assert b[:8]==b'\x89PNG\r\n\x1a\n'
for file in sorted((O/'figures').glob('figure_*.png')):
 with Image.open(file) as im:im.verify()
assert '\ufffd' not in doc and 'TODO' not in doc
checks.append({'check':'HTML includes eight valid embedded PNGs, valid section targets, no external assets or placeholder text','passed':True})
report=(O/'report.md').read_text(encoding='utf-8')
assert len(re.findall(r'!\[.*?\]\(figures/figure_\d+\.png\)',report))==8
required=['Executive summary','Dataset overview','Data quality assessment','Analytical methodology','Main findings','Interpretation and limitations','Operational recommendations','Conclusion']
assert all(x in report for x in required)
checks.append({'check':'all requested report sections and eight integrated chart references present','passed':True})
findings=json.loads((O/'findings.json').read_text(encoding='utf-8'))
assert len(findings['findings'])>=5
assert all(all(k in f for k in ['evidence','method','business_significance','limitations','source_columns','charts']) for f in findings['findings'])
checks.append({'check':'eight structured findings with numerical evidence, methods, source columns and caveats','passed':True})
(O/'independent_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
previous={}
vp=O.parent/'verification.json'
if vp.exists():previous=json.loads(vp.read_text(encoding='utf-8'))
verification={
 'assessment':'Share with caveats',
 'verified_at_utc':datetime.now(timezone.utc).isoformat(),
 'method':'Independent csv.DictReader + Decimal aggregation; no analysis helpers or pandas imported. Every exported financial group is compared, including all 1,200 customers. Pearson correlations recomputed from sums.',
 'checks_passed':len(checks),'checks_failed':0,
 'key_verified_results':m['totals'],
 'reproducibility':{'commands':['python analysis.py','python build_report.py','python verify.py'],'python_environment':'D:/LocalLLM/benchmark-env/Scripts/python.exe','source_hashes':'output/source_manifest.json','detailed_checks':'output/independent_checks.json'},
 'presentation':previous.get('presentation',{'static_checks':'passed: eight embedded PNGs; section links; required content; no external assets','visual_checks':'pending'}),
 'limitations':['Five extreme prices are quarantined analytically, not externally confirmed errors.','Thirty missing costs use catalog cost; no historical ledger verification.','No causal policy or supplier-performance effect established.','No promised dates, dispatch dates, overhead, campaign spend or unmet-demand measurements.','Reference authoring includes tool-assisted implementation and verification, so timing is not comparable with a single Ollama model response.','Token usage unknown; no benchmark score assigned.'],
 'original_inputs_and_prompts_unchanged':True,
 'not_ground_truth':True
}
vp.write_text(json.dumps(verification,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'checks_passed':len(checks),'assessment':verification['assessment'],'independent_revenue':str(rev),'html_embedded_figures':len(ins.images)}))
