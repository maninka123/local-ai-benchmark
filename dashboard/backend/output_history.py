"""Read-only attempt history and explicitly separate small repaired outputs."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from benchmark.util import ROOT, read_json, artifact_files
from dashboard.backend.modifications import baseline, working_path, workspace
from extensions.completion_reviews import normalized

router=APIRouter(prefix='/api/outputs')

def readiness(task,scores):
    evidence=(scores or {}).get('evidence',{});browser=evidence.get('browser') or {}
    if task=='racing_game':
        built=evidence.get('build_success') is True or browser.get('build') is True
        errors=browser.get('errors') or []
        return 'Build failed' if not built else 'Preview opens; recorded runtime errors' if errors else 'Preview opens; game canvas missing' if browser.get('checks',{}).get('canvas') is False else 'Saved scene can be previewed'
    if task=='data_analysis':
        reproduction=evidence.get('reproducibility') or {}
        return 'Analysis script runs' if reproduction.get('executed') and reproduction.get('exit_code')==0 else 'Analysis did not reproduce successfully'
    return 'Inspect the saved report and evidence files'

def stage(number,name,task,scores,completed,error=None,basis='',update_id=None,status=None):
    outcome='complete' if completed is True else 'failed' if completed is False or error else 'working' if status in ['queued','running','launching','interrupted'] else 'unreviewed'
    return {'number':number,'name':name,'outcome':outcome,'readiness':readiness(task,scores),'error':error,'basis':basis,'update_id':update_id}

def repairs_for(row):
    folder=working_path(row)/'repairs';items=[]
    for path in sorted(folder.glob('*/repair.json')):
        info=read_json(path,{})
        if info.get('run_id')!=row['run_id']:continue
        files=[p.relative_to(path.parent/'artifacts').as_posix() for p in artifact_files(path.parent/'artifacts')]
        items.append({**info,'repair_id':path.parent.name,'files':files})
    return items

@router.get('/{run_id}/history')
def history(run_id:str):
    row=baseline(run_id);base=ROOT/'results/improvement_campaign'
    group={'data_analysis':'data','racing_game':'racing','detective':'detective'}[row['task']]
    initial=next((r for r in read_json(base/(group+'_reviews.json'),[]) if r.get('run_id')==run_id),{})
    items=[stage(1,'Initial result',row['task'],row.get('original_scores',row.get('scores')),initial.get('initial_completed'),row.get('error'))]
    current=workspace(run_id).get('revision') or {};used=[]
    for number,folder in [(2,base),(3,base/'pass_2')]:
        entry=next((e for e in read_json(folder/'campaign.json',{}).get('entries',[]) if e['run_id']==run_id),{})
        if not entry.get('update_id'):continue
        used.append(entry['update_id']);review=normalized(entry.get('final_review') or {})
        prompt=next((p for p in current.get('prompts',[]) if p['update_id']==entry['update_id']),{})
        items.append(stage(number,'First improvement' if number==2 else 'Second improvement',row['task'],(entry.get('evaluation') or {}).get('scores'),review.get('completed'),prompt.get('error'),review['completion_basis'],entry['update_id'],entry.get('status')))
    from dashboard.backend.judging import reviewed_rows
    judged=next((r for r in reviewed_rows() if r['run_id']==run_id),{})
    by_number={a['number']:a for a in judged.get('attempts',[])}
    items=[{**a,'judgment':by_number.get(a['number'])} for a in items]
    return {'run_id':run_id,'attempts':items,'other_saved_updates':sum(p['update_id'] not in used for p in current.get('prompts',[])),'repairs':repairs_for(row),'note':'Attempts 1–3 are the initial result and the two benchmark improvements. Other manual/setup requests are separate. A runnable preview does not mean the whole task is complete.'}

def repair_location(run_id,repair_id):
    row=baseline(run_id);base=(working_path(row)/'repairs').resolve();path=(base/repair_id).resolve()
    if not path.is_relative_to(base) or path.parent!=base or not (path/'repair.json').is_file():raise HTTPException(404,'Repair not found')
    info=read_json(path/'repair.json',{})
    if info.get('run_id')!=run_id:raise HTTPException(404,'Repair not found')
    return path,info

@router.get('/{run_id}/repairs/{repair_id}/file/{name:path}')
def repair_file(run_id:str,repair_id:str,name:str):
    path,_=repair_location(run_id,repair_id);base=(path/'artifacts').resolve();file=(base/name).resolve()
    if not file.is_relative_to(base) or not file.is_file() or file.is_symlink():raise HTTPException(404,'File unavailable')
    if file.suffix.lower() in ['.png','.jpg','.jpeg']:return FileResponse(file)
    if file.stat().st_size>5_000_000:raise HTTPException(413,'Large file; inspect locally')
    text=file.read_text(encoding='utf-8',errors='replace')
    if file.suffix.lower()=='.md':
        from markdown_it import MarkdownIt
        body=MarkdownIt('commonmark',{'html':False}).enable('table').render(text)
        return HTMLResponse('<meta charset="utf-8"><style>body{font:18px/1.7 system-ui;padding:28px}img{max-width:100%}</style>'+body,headers={'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'self'"})
    return PlainTextResponse(text)

@router.post('/{run_id}/repairs/{repair_id}/game')
def repair_game(run_id:str,repair_id:str,session_id:str|None=None):
    path,info=repair_location(run_id,repair_id)
    if not isinstance(info.get('source_changed_lines'),int) or not 0<=info['source_changed_lines']<50:raise HTTPException(409,'Repair exceeds the fewer-than-50-lines limit')
    if info.get('task')!='racing_game' or not info.get('runnable'):raise HTTPException(409,'This repaired output is not a verified runnable game preview')
    from dashboard.backend.app import launch_site,viewer_key
    return launch_site(viewer_key('repair-'+run_id+'-'+repair_id,session_id),path/'artifacts/game/dist')

@router.delete('/{run_id}/repairs/{repair_id}/game')
def stop_repair_game(run_id:str,repair_id:str,session_id:str|None=None):
    repair_location(run_id,repair_id)
    from dashboard.backend.app import viewer_lock,remove_viewer,viewer_key
    with viewer_lock:remove_viewer(viewer_key('repair-'+run_id+'-'+repair_id,session_id))
    return {'stopped':True}
