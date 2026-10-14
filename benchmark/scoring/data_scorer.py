import json,re,math
from PIL import Image
from benchmark.util import ROOT,read_json
from benchmark.scoring.writing_scorer import safe_text,writing_evidence,score_result

SECTIONS=['executive summary','dataset|data overview','quality','method','finding','chart|figure','limitation','recommendation','conclusion']

def finding_list(obj):
    if isinstance(obj,list):return obj
    if isinstance(obj,dict):return obj.get('findings',[obj])
    return []

def numeric_match(text,value):
    nums=[]
    for s in re.findall(r'(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?%?',text):
        try:
            n=float(s.replace(',','').replace('%',''));nums.append(n)
            if s.endswith('%'):nums.append(n/100)
        except ValueError:pass
    return any(abs(n-value)<=(0 if isinstance(value,int) else max(.0001,abs(value)*.02)) for n in nums)

def score(run,box=None):
    art=run/'artifacts';truth=read_json(ROOT/'evaluation_private'/'ground_truth'/'business.json');
    report=safe_text(art/'report.md',art);code=safe_text(art/'analysis.py',art);raw=safe_text(art/'findings.json',art)
    try:obj=json.loads(raw)
    except ValueError:obj=[]
    findings=finding_list(obj);patterns=[]
    for p in truth['patterns']:
        matched=[f for f in findings if any(k in json.dumps(f).lower() for k in p['keywords']) and numeric_match(json.dumps(f),p['value'])]
        patterns.append({'id':p['id'],'detected':bool(matched),'expected_metric':p['metric'],'expected_value':p['value'],'matching_findings':matched})
    metrics=obj.get('metrics',{}) if isinstance(obj,dict) else {};numerical=[]
    public_metrics=['total_revenue','profit_margin','clean_row_count','duplicate_count','missing_unit_cost','invalid_quantity_count','entry_outlier_count']
    for key in public_metrics:
        val=truth['metrics'][key]
        tolerance=0 if isinstance(val,int) else max(.0001,abs(val)*.02)
        actual=metrics.get(key);ok=isinstance(actual,(int,float)) and math.isfinite(actual) and abs(actual-val)<=tolerance
        numerical.append({'metric':key,'expected':val,'actual':actual,'correct':ok})
    # Findings can carry matching numeric evidence even when no common metrics dictionary is supplied.
    accuracy=sum(x['correct'] for x in numerical)/len(numerical)
    valid_figures=[]
    for p in (art/'figures').glob('*.png') if (art/'figures').exists() else []:
        if p.is_symlink() or not p.resolve().is_relative_to(art.resolve()):continue
        try:
            with Image.open(p) as im:im.verify()
            valid_figures.append(p.name)
        except Exception:pass
    reproducibility={'executed':False,'exit_code':None}
    if box and code:
        result=box.exec(['python','/output/analysis.py'],category='reproducibility_validation');reproducibility={'executed':True,**result}
    write=writing_evidence(report,SECTIONS)
    cleaning_hits=sum(x['detected'] for x in patterns[:4])
    categories={'data_understanding':15*cleaning_hits/4,'numerical_accuracy':20*accuracy,
        'hidden_patterns':20*sum(x['detected'] for x in patterns)/12,
        'visualization':None if valid_figures else 0,'report_quality':None if report else 0,'recommendations':None if report else 0}
    complete=bool(write['words']>=1400 and all(write['sections'].values()) and len(findings)>=5 and len(valid_figures)>=6 and code and reproducibility.get('exit_code')==0)
    return score_result('data_analysis',categories,{'patterns':patterns,'numeric_checks':numerical,'figures':valid_figures,'writing':write,'reproducibility':reproducibility},complete,
        ['Chart existence is verified; plotted values, visual clarity, substantive writing and recommendations require human review. Data-understanding points are numerical issue checks, not a full understanding assessment.'])
