"""Separate output-only judgments; never modify benchmark scores."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from benchmark.util import ROOT, read_json

router = APIRouter(prefix='/api/judging')
POLICY = {'version':'single-final-score-v2','completion_scores':{'1':100,'2':60,'3':30},
    'description':'One final score per task. Fully completed on attempt 1: 100; attempt 2: 60; attempt 3: 30. If still incomplete after attempt 3, only attempt 3 earns partial credit: its raw rubric quality × 0.30. Earlier failed attempts receive no score.',
    'exclusions':'No runtime, token speed, hardware, Astra reference output or GPT-assisted repairs contribute. Automatic benchmark scores remain preserved. These are AI review judgments, not human ratings.',
    'aggregation':'Final scores are averaged across Detective cases within model and sensory track. Missing results are not zero. Earlier attempts retain status, outputs and review notes, but no awarded score.'}

def reviewed_rows():
    rows=[]
    for name in ['data','racing','detective']:
        for row in read_json(ROOT/'results/judged_scores'/f'{name}.json',[]):
            attempts=[];first_completed=next((a['number'] for a in sorted(row['attempts'],key=lambda a:a['number']) if a['completed']),None)
            final_number=first_completed or max(a['number'] for a in row['attempts'])
            for attempt in sorted(row['attempts'],key=lambda a:a['number']):
                criteria=attempt['criteria']
                if abs(sum(c['max_points'] for c in criteria)-100)>0.01 or any(not 0<=c['points']<=c['max_points'] for c in criteria):
                    raise ValueError('Invalid review rubric: '+row['run_id'])
                raw=sum(c['points'] for c in criteria)
                if abs(raw-attempt['raw_score'])>0.01:raise ValueError('Review total does not match rubric')
                score=(POLICY['completion_scores'][str(first_completed)] if first_completed else round(raw*.30,1)) if attempt['number']==final_number else None
                attempts.append({**attempt,'score':score,'is_final':attempt['number']==final_number})
            final=next(a for a in attempts if a['is_final'])
            rows.append({**row,'attempts':attempts,'first_completed_attempt':first_completed,'final':final})
    return rows

@router.get('')
def judging():
    rows=reviewed_rows();groups={}
    for row in rows:
        key=(row['model'],row['task'],row.get('sensory_track',''))
        groups.setdefault(key,[]).append(row)
    aggregates=[]
    for (model,task,track),items in groups.items():
        aggregates.append({'model':model,'task':task,'sensory_track':track,'cases':len(items),
            'score':round(sum(r['final']['score'] for r in items)/len(items),1),
            'raw_score':round(sum(r['final']['raw_score'] for r in items)/len(items),1),
            'completed':sum(r['final']['completed'] for r in items)})
    return {'policy':POLICY,'rows':rows,'aggregates':aggregates,'reviewed':len(rows),'expected':53}

@router.get('/report',response_class=HTMLResponse)
def report():
    from markdown_it import MarkdownIt
    path=ROOT/'results/judged_scores/review_report.md'
    text=path.read_text(encoding='utf-8') if path.exists() else '# Output reviews\n\nReview report is being prepared.'
    body=MarkdownIt('commonmark',{'html':False}).enable('table').render(text)
    return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Local output reviews</title><style>body{font:18px/1.65 system-ui;color:#1d1d1f;background:#f5f5f7;max-width:1400px;margin:auto;padding:24px}table{display:block;overflow:auto;border-collapse:collapse;background:white}th,td{padding:12px;border:1px solid #d8deea;vertical-align:top;text-align:left}code{overflow-wrap:anywhere}h2{margin-top:48px}</style>'+body)
