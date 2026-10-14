"""Durable, separate revision records and sequential local jobs."""
import os,sys,json,uuid,subprocess,threading,time,datetime,shutil,psutil,re
from pathlib import Path
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import FileResponse,PlainTextResponse,HTMLResponse
from benchmark.util import ROOT,read_json,write_json,now,artifact_files

router=APIRouter(prefix='/api/modifications');BASE=ROOT/'results'/'modifications'
workspace_router=APIRouter(prefix='/api/workspaces');workspace_guard=threading.Lock()
thread=None;guard=threading.Lock()

def processing_paused():return (ROOT/'results/improvement_campaign/stop_requested').exists()

def require_processing():
    if processing_paused():raise HTTPException(423,'Processing is paused to keep GPU and RAM free. Prepare a draft, then resume processing before running an update or evaluation.')

def records():
    paths=[*sorted(BASE.glob('rev-*/revision.json')),*sorted((ROOT/'results'/'further-work').glob('*/*/*/revision.json'))]
    # A migrated working copy keeps its identity; its legacy directory remains archived.
    return list({r['revision_id']:r for p in paths if (r:=read_json(p,{})).get('revision_id')}.values())
def location(revision_id):
    if not revision_id.startswith('rev-') or len(revision_id)!=16 or any(c not in '0123456789abcdef' for c in revision_id[4:]):raise HTTPException(404,'Unknown revision')
    path=next((p.parent for p in (ROOT/'results'/'further-work').glob('*/*/*/revision.json') if read_json(p,{}).get('revision_id')==revision_id),BASE/revision_id)
    if not (path/'revision.json').exists():raise HTTPException(404,'Unknown revision')
    return path

def working_path(row):
    slug=lambda text:re.sub(r'[^a-zA-Z0-9._-]+','-',text).strip('-')[:150]
    path=ROOT/'results'/'further-work'/slug(row['model']['name'])/slug(row['task']+('-'+row['case'] if row.get('case') else ''))/slug(row['run_id'])
    if not path.resolve().is_relative_to((ROOT/'results'/'further-work').resolve()):raise HTTPException(404,'Unknown result folder')
    return path

def prepare_work(row):
    path=working_path(row)
    if (path/'revision.json').exists():return path,read_json(path/'revision.json')
    previous=listing(row['run_id']);latest=previous[-1] if previous else None
    if latest and latest['status'] not in ['finished','failed','interrupted']:raise HTTPException(409,'Wait for the current update to finish.')
    source=location(latest['revision_id']) if latest else ROOT/row['run_path']
    path.mkdir(parents=True,exist_ok=True)
    if latest:
        for p in artifact_files(source):
            target=path/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        info={**latest,'workspace_mode':True,'migrated_from':str(source)}
        info['prompts']=[{'update_id':'imported-'+latest['revision_id'],'name':latest['name'],'prompt':latest['prompt'],'created':latest['created'],'status':latest['generation_status'],'seconds':latest['generation_seconds'],'summary':latest.get('summary'),'changes':latest.get('changes'),'performance':latest.get('performance')}]
    else:
        revision_id='rev-'+uuid.uuid4().hex[:12]
        shutil.copytree(source/'input',path/'input',dirs_exist_ok=True)
        (path/'artifacts').mkdir(exist_ok=True)
        for p in artifact_files(source/'artifacts'):
            target=path/'artifacts'/p.relative_to(source/'artifacts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        write_json(path/'identity.json',{'run_id':revision_id,'model':row['model']['name'],'digest':row['model']['digest'],'task':row['task'],'case':row.get('case'),'sensory_track':row.get('sensory_track'),'created':now()})
        info={'revision_id':revision_id,'name':'Further work','prompt':'','created':now(),'base_run_id':row['run_id'],'parent_revision_id':None,'workspace_mode':True,'prompts':[],
            'model':row['model'],'task':row['task'],'case':row.get('case'),'sensory_track':row.get('sensory_track'),'status':'finished','generation_status':'finished','generation_seconds':0,'performance':{},'evaluations':[],
            'original_scores':read_json(source/'scores.json',row['scores']),'original_seconds':row['task_seconds'],'original_performance':row['performance'],
            'note':'One continuing workspace for all further prompts. Initial output, score and timing are preserved.'}
    write_json(path/'revision.json',info)
    (path/'README.txt').write_text('FURTHER WORK\nAll prompts update artifacts/ in this one workspace.\nPrompt history, cumulative time and tokens are in revision.json.\nInitial results remain at: '+str((ROOT/row['run_path']).resolve())+'\n',encoding='utf-8')
    return path,info

@workspace_router.get('/{run_id}')
def workspace(run_id:str):
    row=baseline(run_id);path=working_path(row);revisions=listing(run_id)
    current=next((r for r in revisions if r.get('workspace_mode')),revisions[-1] if revisions else None)
    return {'run_id':run_id,'initial_folder':str((ROOT/row['run_path']/'artifacts').resolve()),'further_folder':str((path/'artifacts').resolve()),'further_exists':(path/'revision.json').exists(),
        'revision':current,'processing_paused':processing_paused(),'extra_seconds':sum(r['extra_seconds'] for r in revisions),'extra_input_tokens':sum((r.get('performance') or {}).get('input_tokens',0) for r in revisions),
        'extra_output_tokens':sum((r.get('performance') or {}).get('output_tokens',0) for r in revisions)}

@workspace_router.post('/{run_id}/prompt',status_code=202)
def continue_work(run_id:str,payload:dict):
    require_processing()
    row=baseline(run_id);prompt=payload.get('prompt');name=payload.get('name','')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>20000 or not isinstance(name,str) or len(name)>100:raise HTTPException(422,'Provide a prompt up to 20,000 characters and an optional title up to 100 characters.')
    with workspace_guard:
        path,info=prepare_work(row)
        if info['status'] not in ['finished','failed','interrupted']:raise HTTPException(409,'Wait for the current update or evaluation to finish.')
        update={'update_id':'update-'+uuid.uuid4().hex[:10],'name':name.strip() or f"Update {len(info['prompts'])+1}",'prompt':prompt.strip(),'created':now(),'status':'queued','seconds':0}
        info['prompts'].append(update)
        info.update(prompt=update['prompt'],name=update['name'],status='queued',generation_status='queued',error=None,operation='update',current_update_id=update['update_id'])
        write_json(path/'revision.json',info)
    start_queue();return workspace(run_id)

@workspace_router.post('/{run_id}/open-folder')
def open_folder(run_id:str,payload:dict,request:Request):
    origin=request.headers.get('origin')
    if request.headers.get('sec-fetch-site')=='cross-site' or (origin and origin not in [str(request.base_url).rstrip('/'),str(request.base_url).rstrip('/').replace('127.0.0.1','localhost')]):raise HTTPException(403,'Open folders from this local dashboard.')
    row=baseline(run_id);kind=payload.get('kind')
    if kind=='initial':folder=ROOT/row['run_path']/'artifacts'
    elif kind=='further':
        with workspace_guard:path,_=prepare_work(row)
        folder=path/'artifacts'
    else:raise HTTPException(422,'Choose initial or further results.')
    if not folder.resolve().is_relative_to(ROOT.resolve()) or not folder.is_dir():raise HTTPException(404,'Result folder unavailable')
    try:os.startfile(str(folder.resolve()))
    except (OSError,AttributeError) as e:raise HTTPException(500,'Could not open File Explorer: '+str(e))
    return {'opened':True,'path':str(folder.resolve())}
def baseline(run_id):
    row=next((r for r in read_json(ROOT/'results'/'master_results.json',[]) if r['run_id']==run_id),None)
    if not row:raise HTTPException(404,'Unknown benchmark attempt')
    return row
def elapsed(row):
    if row.get('status') in ['running','reevaluating'] and row.get('operation_start'):
        return max(0,(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(row['operation_start'])).total_seconds())
    return 0
def safe_artifact(path,name):
    base=path/'artifacts';target=base/name
    try:
        if target.is_symlink() or not target.resolve().is_relative_to(base.resolve()) or not target.is_file():raise HTTPException(404,'Artifact unavailable')
    except OSError:raise HTTPException(404,'Artifact unavailable')
    return target

@router.get('')
def listing(run_id:str|None=None):
    rows=[r for r in records() if not run_id or r['base_run_id']==run_id]
    for row in rows:
        row['active_seconds']=elapsed(row)
        row['extra_seconds']=row.get('generation_seconds',0)+sum(e['seconds'] for e in row.get('evaluations',[]))+row['active_seconds']
    return sorted(rows,key=lambda r:r['created'])

@router.post('',status_code=202)
def create(payload:dict):
    require_processing()
    row=baseline(payload.get('run_id'))
    if not isinstance(payload.get('name'),str) or not isinstance(payload.get('prompt'),str):raise HTTPException(422,'Provide a revision name and prompt as text.')
    name=payload['name'].strip();prompt=payload['prompt'].strip()
    if not name or len(name)>100 or not prompt or len(prompt)>20000:raise HTTPException(422,'Provide a revision name (up to 100 characters) and prompt (up to 20,000 characters).')
    parent=payload.get('parent_revision_id');source=ROOT/row['run_path']
    if parent:
        source=location(parent);info=read_json(source/'revision.json')
        if info['base_run_id']!=row['run_id'] or info['status'] not in ['finished','failed','interrupted']:raise HTTPException(409,'Choose a finished revision from this benchmark attempt.')
    revision_id='rev-'+uuid.uuid4().hex[:12];path=BASE/revision_id
    (path/'input').mkdir(parents=True);(path/'artifacts').mkdir()
    shutil.copytree(source/'input',path/'input',dirs_exist_ok=True)
    for p in artifact_files(source/'artifacts'):
        target=path/'artifacts'/p.relative_to(source/'artifacts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    write_json(path/'identity.json',{'run_id':revision_id,'model':row['model']['name'],'digest':row['model']['digest'],'task':row['task'],'case':row.get('case'),'sensory_track':row.get('sensory_track'),'created':now()})
    info={'revision_id':revision_id,'name':name,'prompt':prompt,'created':now(),'base_run_id':row['run_id'],'parent_revision_id':parent,
        'model':row['model'],'task':row['task'],'case':row.get('case'),'sensory_track':row.get('sensory_track'),'status':'queued','generation_status':'queued','generation_seconds':0,'evaluations':[],
        'original_scores':read_json(ROOT/row['run_path']/'scores.json',row['scores']),'original_seconds':row['task_seconds'],'original_performance':row['performance'],
        'note':'User-prompted revision; excluded from original benchmark rankings. Original files, score and timing are immutable.'}
    write_json(path/'revision.json',info);start_queue();return info

@router.get('/{revision_id}')
def detail(revision_id:str,after:int=0,tail:int=0):
    path=location(revision_id);info=read_json(path/'revision.json');events=[];count=0
    stream=path/'live_events.jsonl'
    if stream.exists():
        for line in stream.read_text(encoding='utf-8').splitlines():
            try:event=json.loads(line)
            except ValueError:continue
            if count>=max(0,after):events.append(event)
            count+=1
    if tail>0 and after==0:events=events[-min(tail,1000):]
    tools=[];log=path/'tool_calls.jsonl'
    if log.exists():
        for line in log.read_text(encoding='utf-8').splitlines():
            try:tools.append(json.loads(line))
            except ValueError:pass
    return {'revision':info,'files':[p.relative_to(path/'artifacts').as_posix() for p in artifact_files(path/'artifacts')],
        'events':events,'next_cursor':count,'tools':tools[-40:],'active_seconds':elapsed(info)}

@router.post('/{revision_id}/evaluate',status_code=202)
def evaluate(revision_id:str):
    require_processing()
    with workspace_guard:
        path=location(revision_id);info=read_json(path/'revision.json')
        if info['status'] not in ['finished','failed','interrupted']:raise HTTPException(409,'Wait for the current operation to finish.')
        info['status']='queued_score';write_json(path/'revision.json',info)
    start_queue();return info

@router.get('/{revision_id}/artifact/{name:path}')
def artifact(revision_id:str,name:str):
    path=safe_artifact(location(revision_id),name)
    if path.suffix.lower() in ['.png','.jpg','.jpeg']:return FileResponse(path)
    if path.stat().st_size>5_000_000:raise HTTPException(413,'Inspect this large file locally.')
    return PlainTextResponse(path.read_text(encoding='utf-8',errors='replace'))

@router.get('/{revision_id}/report/{name:path}')
def report(revision_id:str,name:str):
    from markdown_it import MarkdownIt
    path=safe_artifact(location(revision_id),name)
    if path.suffix.lower()!='.md' or path.stat().st_size>1_000_000:raise HTTPException(422,'Choose a Markdown report.')
    body=MarkdownIt('commonmark',{'html':False}).enable('table').render(path.read_text(encoding='utf-8',errors='replace'))
    return HTMLResponse('<!doctype html><meta charset="utf-8"><base href="/api/modifications/'+revision_id+'/artifact/"><style>body{font:18px/1.7 system-ui;padding:28px;color:#24344a}img{max-width:100%}pre{overflow:auto}</style>'+body,
        headers={'Content-Security-Policy':"default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; frame-ancestors 'self'; form-action 'none'"})

@router.get('/{revision_id}/log/{name}')
def log(revision_id:str,name:str):
    if name not in ['live_events.jsonl','inference_calls.jsonl','tool_calls.jsonl','execution_trace.jsonl','hardware_metrics.csv','revision.json','error.txt']:raise HTTPException(404,'Unknown log')
    path=location(revision_id);target=path/name
    if not target.is_file() or target.is_symlink():raise HTTPException(404,'Log unavailable')
    return FileResponse(target,media_type='text/plain',filename=name)

def queue():
    while True:
        if processing_paused():time.sleep(2);continue
        active=False
        for info in records():
            if info['status'] in ['launching','running','reevaluating']:
                if psutil.pid_exists(info.get('worker_pid',-1)):active=True
                else:
                    seconds=elapsed(info)
                    if info.get('operation')=='score':info.setdefault('evaluations',[]).append({'evaluation_id':'interrupted-'+uuid.uuid4().hex[:10],'timestamp':now(),'seconds':seconds,'scores':None,'error':'Worker interrupted before scoring finished.'})
                    else:info['generation_seconds']=info.get('generation_seconds',0)+seconds
                    info.pop('operation_start',None)
                    info['status']='interrupted';info['error']='Worker stopped; partial artifacts and logs are preserved.'
                    if info.get('operation')=='update' and info.get('prompts'):
                        info['prompts'][-1].update(status='interrupted',seconds=seconds,error=info['error'])
                    if info.get('operation')=='update':info['generation_status']='interrupted'
                    write_json(location(info['revision_id'])/'revision.json',info)
        gpu=read_json(ROOT/'logs'/'gpu-controller.lock',{})
        if active or (gpu and psutil.pid_exists(gpu.get('pid',-1))):time.sleep(2);continue
        queued=sorted((r for r in records() if r['status'] in ['queued','queued_score']),key=lambda r:r['created'])
        if not queued:time.sleep(2);continue
        info=queued[0];operation='score' if info['status']=='queued_score' else 'update';path=location(info['revision_id'])
        try:
            proc=subprocess.Popen([sys.executable,str(ROOT/'scripts'/'revision_worker.py'),'--revision',info['revision_id'],'--operation',operation],cwd=ROOT,
                stdout=(path/f'{operation}.stdout.log').open('a'),stderr=(path/f'{operation}.stderr.log').open('a'),creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            info.update(status='launching',worker_pid=proc.pid,operation=operation);write_json(path/'revision.json',info)
        except Exception as e:info.update(status='failed',error=str(e));write_json(path/'revision.json',info)
        time.sleep(2)

def start_queue():
    global thread
    with guard:
        if thread is None or not thread.is_alive():thread=threading.Thread(target=queue,daemon=True);thread.start()
