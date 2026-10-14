from pathlib import Path
import json,sqlite3,subprocess,socket,uuid,time,atexit,datetime,psutil,threading
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse,PlainTextResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from benchmark.util import ROOT,read_json,now,source_hash,artifact_files
from dashboard.backend.modifications import router as revision_router,workspace_router,start_queue,listing as revision_listing
from dashboard.backend.parameters import enrich
from dashboard.backend.completion_pass import router as completion_router
from dashboard.backend.references import router as reference_router
from dashboard.backend.output_history import router as output_router
from dashboard.backend.judging import router as judging_router
from extensions import text_detective

@asynccontextmanager
async def lifespan(app):
    start_queue()
    yield
    cleanup()

app=FastAPI(title='Local LLM Benchmark',docs_url='/api/docs',lifespan=lifespan);viewers={};viewer_lock=threading.RLock()
app.include_router(revision_router)
app.include_router(workspace_router)
app.include_router(completion_router)
app.include_router(reference_router)
app.include_router(output_router)
app.include_router(judging_router)

@app.middleware('http')
async def local_headers(request,call_next):
    response=await call_next(request)
    if 'content-security-policy' not in response.headers:
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; frame-src http://127.0.0.1:*; object-src 'none'; base-uri 'self'; form-action 'self'"
    response.headers['X-Content-Type-Options']='nosniff'
    return response

def runs():return read_json(ROOT/'results'/'master_results.json',[])
def find(run_id):
    for row in runs():
        if row['run_id']==run_id:return row
    raise HTTPException(404,'Unknown run')

def run_path(run_id):return ROOT/find(run_id)['run_path']

def safe(path,base):
    resolved=path.resolve()
    if path.is_symlink() or not resolved.is_relative_to(base.resolve()) or not resolved.is_file():raise HTTPException(404,'File unavailable')
    return resolved

@app.get('/api/improvement-report-data')
def improvement_report_data():
    from extensions.improvement_reporting import receipt
    return receipt()

@app.get('/api/benchmark-report',response_class=HTMLResponse)
def benchmark_report():
    from extensions.improvement_reporting import receipt,section
    from markdown_it import MarkdownIt
    data=receipt()
    content=MarkdownIt().enable('table').render('# Local benchmark results\n\n'+section(data))
    return HTMLResponse('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local benchmark results</title><style>*{box-sizing:border-box}body{overflow-wrap:anywhere;font:18px/1.6 system-ui;color:#1d1d1f;background:#f5f5f7;max-width:1500px;margin:auto;padding:2rem}table{display:block;width:100%;max-width:100%;overflow:auto;background:white;border-collapse:collapse}th,td{padding:.8rem;border:1px solid #d0d7e1;text-align:left;vertical-align:top}h2,h3,h4{line-height:1.3;margin-top:2rem}h4{padding-top:1rem;border-top:1px solid #d0d7e1}a{color:#0064c9}code{overflow-wrap:anywhere}ul{padding-left:1.4rem}@media(max-width:700px){body{padding:1rem}}</style></head><body>'+content+'</body></html>')

@app.get('/api/summary')
def summary():
    models=read_json(ROOT/'models'/'discovered.json',{}).get('models',[])
    lock=read_json(ROOT/'logs'/'gpu-controller.lock')
    alive=bool(lock and psutil.pid_exists(lock.get('pid',-1)))
    displayed=[enrich(m) for m in models];by_digest={m['digest']:m for m in displayed}
    from dashboard.backend.judging import reviewed_rows
    judged={r['run_id']:{'initial':r['attempts'][0],'latest':r['final']} for r in reviewed_rows()}
    rows=[{**r,'output_review':judged.get(r['run_id']),'model':{**r['model'],'parameter_comparison':by_digest.get(r['model']['digest'],{}).get('parameter_comparison'),'input_video':by_digest.get(r['model']['digest'],{}).get('input_video')}} for r in runs()]
    return {'models':displayed,
        'runs':rows,'environment':read_json(ROOT/'results'/'environment.json'),
        'aggregates':read_json(ROOT/'results'/'aggregates.json',[]),'setup':read_json(ROOT/'results'/'setup_validation.json'),
        'running':lock if alive and lock.get('kind')!='revision' else None,'generated_at':now(),'active_protocol':source_hash(),
        'modifications':[{**v,'model':{**v['model'],'input_video':by_digest.get(v['model']['digest'],{}).get('input_video')}} for v in revision_listing()],'progress':progress(alive and (lock or {}).get('kind')!='revision'),'campaign':read_json(ROOT/'results'/'active_campaign.json')}

def progress(alive):
    campaign=read_json(ROOT/'results'/'active_campaign.json',{})
    entries=campaign.get('entries',[])
    current=read_json(ROOT/'logs'/'current_task.json',{})
    if not campaign:
        history=runs();baseline=history[-1]['protocol_hash'] if history else None
        completed=[r for r in history if r.get('protocol_hash')==baseline]
        models=read_json(ROOT/'models'/'discovered.json',{}).get('models',[])
        total=sum(5 if m['vision'] else 2 for m in models)
        entries=[{'status':'done','retry':False} for _ in completed]+[{'status':'pending','retry':False} for _ in range(max(0,total-len(completed)))]
        if alive:
            identities=list((ROOT/'models').glob('*/*/*/identity.json'))
            if identities:
                path=max(identities,key=lambda p:p.stat().st_mtime)
                if not (path.parent/'result.json').exists():
                    identity=read_json(path,{});calls=jsonl(path.parent/'inference_calls.jsonl')
                    limit=completed[-1]['config']['benchmark']['task_timeout_seconds'] if completed else 1800
                    current={'active':True,'model':identity['model'],'task':identity['task'],'case':identity.get('case'),'stage':'Model inference','completed_calls':len(calls),'max_calls':24,'start':identity['created'],'limit_seconds':limit}
    if not current or not current.get('active'):
        current=None
    if current and alive:
        start=current.get('inference_start',current['start'])
        elapsed=max(0,(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(start)).total_seconds())
        current={**current,'elapsed_seconds':elapsed,'budget_percent':min(100,100*elapsed/current['limit_seconds'])}
    else:current=None
    done=sum(e['status']=='done' for e in entries);total=len(entries)
    return {'finished':done,'total':total,'percent':100*done/total if total else 0,
        'retries':sum(bool(e.get('retry')) and e.get('retry_kind')!='compatibility_recovery' for e in entries),'state':'interrupted' if campaign.get('status')=='running' and not alive else campaign.get('status','running' if alive else 'idle'),'current':current}

@app.get('/api/run/{run_id}')
def detail(run_id:str):
    run=run_path(run_id);files=[]
    for p in artifact_files(run/'artifacts'):files.append(p.relative_to(run/'artifacts').as_posix())
    return {'result':find(run_id),'files':files,'agent':read_json(run/'agent_state.json'),
        'calls':jsonl(run/'inference_calls.jsonl'),'tools':jsonl(run/'tool_calls.jsonl')}

def jsonl(path):
    if not path.exists():return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

@app.get('/api/run/{run_id}/hardware')
def hardware(run_id:str):
    import csv
    path=run_path(run_id)/'hardware_metrics.csv'
    return list(csv.DictReader(path.open(encoding='utf-8'))) if path.exists() else []

@app.get('/api/run/{run_id}/artifact/{name:path}')
def artifact(run_id:str,name:str):
    base=run_path(run_id)/'artifacts';path=safe(base/name,base)
    if path.suffix.lower() in ['.png','.jpg','.jpeg']:return FileResponse(path)
    if path.stat().st_size>5_000_000:raise HTTPException(413,'Large file; inspect it locally')
    return PlainTextResponse(path.read_text(encoding='utf-8',errors='replace'))

@app.get('/api/run/{run_id}/report/{name:path}')
def render_report(run_id:str,name:str):
    from markdown_it import MarkdownIt
    import html
    base=run_path(run_id)/'artifacts';path=safe(base/name,base)
    if path.suffix.lower()!='.md' or path.stat().st_size>1_000_000:raise HTTPException(422,'Choose a Markdown report')
    body=MarkdownIt('commonmark',{'html':False}).enable('table').render(path.read_text(encoding='utf-8',errors='replace'))
    content='<!doctype html><meta charset="utf-8"><base href="/api/run/'+run_id+'/artifact/"><style>body{font:18px/1.75 system-ui;overflow-wrap:anywhere;color:#24344a;background:#fff;padding:32px;max-width:1000px;margin:auto}img{max-width:100%}pre{overflow:auto;background:#eef2f6;padding:14px}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:8px}a{color:#176088}</style>'+body
    return HTMLResponse(content,headers={'Content-Security-Policy':"default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; frame-ancestors 'self'; form-action 'none'",'X-Content-Type-Options':'nosniff'})

@app.get('/api/run/{run_id}/log/{name}')
def log(run_id:str,name:str):
    if name not in ['inference_calls.jsonl','tool_calls.jsonl','execution_trace.jsonl','hardware_metrics.csv','performance.json','scores.json','error.txt']:raise HTTPException(404)
    path=safe(run_path(run_id)/name,run_path(run_id));return FileResponse(path,media_type='text/plain',filename=name)

@app.get('/api/run/{run_id}/ground-truth')
def ground_truth(run_id:str):
    row=find(run_id)
    if not row.get('scores'):raise HTTPException(409,'Available only after scoring')
    name='business.json' if row['task']=='data_analysis' else row.get('case','')+'.json'
    return read_json(ROOT/'evaluation_private'/'ground_truth'/name,{})

@app.get('/api/run/{run_id}/review-guide')
def review_guide(run_id:str):
    row=find(run_id);task=row['task'];text=(ROOT/'evaluation_private'/'scoring_config'/'human_rubric.md').read_text(encoding='utf-8')
    section={'data_analysis':'Data','racing_game':'Game','detective':'Detective'}[task]
    guide=text.split('## '+section+'\n',1)[1].split('\n## ',1)[0]
    common=text.split('## Data',1)[0]
    text_only=row.get('sensory_track')==text_detective.TRACK
    if text_only:guide=text_detective.REVIEW_GUIDE
    return {'rubric':row['scores']['rubric'],'categories':row['scores']['categories'],'guide':common+'\n'+guide,
        'task_prompt':text_detective.prompt() if text_only else (ROOT/'benchmark'/'prompts'/(task+'_prompt.md')).read_text(encoding='utf-8'),
        'where':{'data_analysis':['report.md','analysis.py','findings.json','figures/'],'racing_game':['game/','screenshots/','browser_validation.json','implementation_report.md'],'detective':['investigation_report.md','timeline.json','evidence_analysis.json','conclusions.json']}[task],
        'instructions':'Open the listed artifacts, compare the observations with each rubric requirement, and assign 0 to the maximum points per category. Include filenames and observations in your reason. Only mark completion when all required behavior has been checked. The original automatic score is retained.'}

@app.post('/api/run/{run_id}/review')
def review(run_id:str,payload:dict):
    from benchmark.scoring.writing_scorer import RUBRICS
    from benchmark.util import append_json
    row=find(run_id);scores=payload.get('categories');reason=payload.get('reason');reviewer=payload.get('reviewer')
    if not reason or not reviewer or not isinstance(scores,dict):raise HTTPException(422,'Provide reviewer, reason and all category values')
    rubric=text_detective.RUBRIC if row.get('sensory_track')==text_detective.TRACK else RUBRICS[row['task']]
    if set(scores)!=set(rubric) or any(not isinstance(v,(int,float)) or not 0<=v<=rubric[k] for k,v in scores.items()):raise HTTPException(422,'Categories must match the rubric and remain within bounds')
    import hashlib
    audit={'run_id':run_id,'timestamp':now(),'reviewer':reviewer,'reason':reason,'original_scores':row['scores'],'reviewed_categories':scores,'quality_score':sum(scores.values()),'complete':bool(payload.get('complete')),
        'rubric_sha256':text_detective.protocol() if row.get('sensory_track')==text_detective.TRACK else hashlib.sha256((ROOT/'evaluation_private'/'scoring_config'/'human_rubric.md').read_bytes()).hexdigest()}
    append_json(run_path(run_id)/'manual_reviews.jsonl',audit)
    with sqlite3.connect(ROOT/'results'/'benchmark.sqlite') as db:
        db.execute('INSERT INTO reviews(run_id,timestamp,reviewer,original_json,corrected_json,reason) VALUES(?,?,?,?,?,?)',(run_id,audit['timestamp'],reviewer,json.dumps(row['scores']),json.dumps(audit),reason))
    from benchmark.scoring.aggregate_scorer import export
    export()
    return audit

@app.post('/api/run/{run_id}/game')
def launch_game(run_id:str,session_id:str|None=None):
    row=find(run_id);run=run_path(run_id);dist=run/'artifacts'/'game'/'dist'
    if row['task']!='racing_game' or not has_game_build(row.get('scores')):raise HTTPException(409,'The saved game did not compile. Inspect its source files and build result.')
    return launch_site(viewer_key(run_id,session_id),dist)

@app.post('/api/modifications/{revision_id}/game')
def launch_revision_game(revision_id:str,evaluation_id:str|None=None,session_id:str|None=None):
    from dashboard.backend.modifications import location
    info=read_json(location(revision_id)/'revision.json')
    evaluations=info.get('evaluations',[])
    latest=next((e for e in evaluations if e.get('evaluation_id')==evaluation_id),None) if evaluation_id else (evaluations[-1] if evaluations else {})
    if latest is None:raise HTTPException(404,'Saved game evaluation not found.')
    if not evaluation_id and info.get('workspace_mode') and latest.get('update_id')!=info.get('current_update_id'):raise HTTPException(409,'Re-evaluate the current work before opening its game build, or choose a saved evaluation.')
    if info['task']!='racing_game' or not has_game_build(latest.get('scores')):raise HTTPException(409,'The saved game did not compile. Inspect its source files and build result.')
    if not latest.get('snapshot_path') or not latest.get('evaluation_id'):raise HTTPException(409,'The saved evaluation has no game snapshot.')
    snapshot=(ROOT/latest['snapshot_path']).resolve()
    if not snapshot.is_relative_to(location(revision_id).resolve()/'evaluations'):raise HTTPException(409,'Invalid saved game snapshot.')
    dist=snapshot/'artifacts'/'game'/'dist'
    return launch_site(viewer_key(revision_id+'-'+latest['evaluation_id'],session_id),dist)

def viewer_key(view_id,session_id=None):
    if session_id is None:return view_id
    if len(session_id)!=32 or any(c not in '0123456789abcdef' for c in session_id):raise HTTPException(422,'Invalid preview session')
    return view_id+'-'+session_id

def has_game_build(scores):
    evidence=(scores or {}).get('evidence',{})
    # A compiled placeholder may fail the implementation rubric, but it is
    # still useful to inspect its saved browser output. Scores are unchanged.
    return evidence.get('build_success') is True or (evidence.get('browser') or {}).get('build') is True

def launch_site(view_id,dist):
    dist=dist.resolve()
    if not dist.is_relative_to(ROOT.resolve()) or not (dist/'index.html').is_file():raise HTTPException(409,'This evaluated build has no playable page. Check its output files and build result.')
    with viewer_lock:return _launch_site(view_id,dist)

def viewer_ready(url):
    try:return httpx.get(url,timeout=1,trust_env=False).status_code==200
    except httpx.HTTPError:return False

def _launch_site(view_id,dist):
    cached=viewers.get(view_id)
    if cached:
        if viewer_ready(cached['url']):return cached
        remove_viewer(view_id)
    name='llmb-view-'+uuid.uuid4().hex[:12]
    # Only trusted static-server code runs here. Generated JS runs in an opaque-origin
    # iframe with CSP, and the dashboard CSP prevents external frame navigation.
    args=['docker','run','-d','--name',name,'--network','bridge','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
        '--memory','1g','--cpus','2','--pids-limit','64','--user','1000:1000','--tmpfs','/tmp:rw,size=64m',
        '-p','127.0.0.1::8000','--mount',f'type=bind,source={dist},target=/site,readonly',
        'local-llm-benchmark:1.0','python','/opt/lab/viewer_server.py']
    try:
        proc=subprocess.run(args,capture_output=True,text=True,timeout=30)
        if proc.returncode:raise HTTPException(503,'Game preview could not start. Check that Docker is running. '+proc.stderr[-600:])
        mapping=subprocess.run(['docker','port',name,'8000/tcp'],capture_output=True,text=True,timeout=10)
        address=mapping.stdout.strip()
        if mapping.returncode or not address.startswith('127.0.0.1:') or not address.split(':')[-1].isdigit():raise HTTPException(503,'Game preview port is unavailable.')
        url='http://'+address
        deadline=time.monotonic()+10
        while not viewer_ready(url):
            if time.monotonic()>=deadline:raise HTTPException(503,'Game preview did not become ready. Try opening it again.')
            time.sleep(.2)
        viewers[view_id]={'url':url,'container':name,'view_id':view_id,'isolation':'Read-only evaluated build in an isolated local viewer. Build success does not certify full game completion.'}
        return viewers[view_id]
    except (OSError,subprocess.TimeoutExpired) as error:
        raise HTTPException(503,'Game preview service is unavailable. Check Docker and try again.') from error
    finally:
        if view_id not in viewers:
            try:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
            except (OSError,subprocess.TimeoutExpired):pass

def remove_viewer(view_id):
    value=viewers.pop(view_id,None)
    if value:
        try:subprocess.run(['docker','rm','-f',value['container']],capture_output=True,timeout=10)
        except (OSError,subprocess.TimeoutExpired):pass

@app.delete('/api/run/{run_id}/game')
def stop_game(run_id:str,session_id:str|None=None):
    with viewer_lock:remove_viewer(viewer_key(run_id,session_id))
    return {'stopped':True}

@app.delete('/api/modifications/{revision_id}/game')
def stop_revision_game(revision_id:str,evaluation_id:str|None=None,session_id:str|None=None):
    from dashboard.backend.modifications import location
    location(revision_id)
    with viewer_lock:
        for key in list(viewers):
            matches=key==viewer_key(revision_id+'-'+evaluation_id,session_id) if evaluation_id else key.startswith(revision_id+'-') and (session_id is None or key.endswith('-'+session_id))
            if matches:remove_viewer(key)
    return {'stopped':True}

def cleanup():
    with viewer_lock:
        for key in list(viewers):remove_viewer(key)
atexit.register(cleanup)
dist=ROOT/'dashboard'/'frontend'/'dist'
if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='dashboard')
