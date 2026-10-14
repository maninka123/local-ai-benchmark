"""Add the three authorized written-evidence Detective baselines, once each."""
import _bootstrap
import hashlib,json,os
import psutil
from benchmark.util import ROOT,read_json,write_json,now,config,artifact_files
from benchmark.harness.model_discovery import discover
from benchmark.scoring.aggregate_scorer import export
from extensions import text_detective
from run_additional_models import attempt

BASE=ROOT/'results/improvement_campaign'
PLAN=BASE/'missing_initials.json'
MODELS=['glm-4.7-flash:q4_K_M','laguna-xs.2:q4_K_M','nemotron-3-nano:30b-a3b-q4_K_M']
CAMPAIGN='missing-written-detective-initials-2026-10-12'

def initialize():
    if not PLAN.exists():write_json(PLAN,{'created':now(),'entries':[{'model':name,'task':'detective','case':'case_03','repetition':1,'sensory_track':text_detective.TRACK,'status':'pending'} for name in MODELS]})

def append_result(row,campaign):
    inventory=read_json(BASE/'baseline_inventory.json',[])
    if not any(r['run_id']==row['run_id'] for r in inventory):
        inventory.append(row);write_json(BASE/'baseline_inventory.json',inventory)
    if not any(e['run_id']==row['run_id'] for e in campaign['entries']):
        campaign['entries'].append({'run_id':row['run_id'],'model':row['model']['name'],'task':row['task'],'case':row['case'],'sensory_track':text_detective.TRACK,'status':'awaiting_review'})
    fingerprints=read_json(BASE/'initial_fingerprints.json',{})
    run=ROOT/row['run_path']
    for path in [run/'result.json',run/'scores.json',*artifact_files(run/'artifacts')]:
        if path.is_file():fingerprints.setdefault(str(path.relative_to(ROOT)),hashlib.sha256(path.read_bytes()).hexdigest())
    write_json(BASE/'initial_fingerprints.json',fingerprints)

def run_next(campaign):
    """Run only when the completion controller has no active improvement."""
    initialize();plan=read_json(PLAN)
    saved_ids={e['run_id'] for e in campaign['entries']}
    entry=next((e for e in plan['entries'] if e['status']!='done' or (e.get('run_id') and e['run_id'] not in saved_ids)),None)
    if not entry:return False
    if config()['benchmark']['task_timeout_seconds']!=3600:raise RuntimeError('Expected the saved one-hour task limit')
    # Recover a saved result if the process stopped after the task finished.
    export()
    rows=read_json(ROOT/'results/master_results.json',[])
    row=next((r for r in reversed(rows) if r.get('campaign')==CAMPAIGN and r['model']['name']==entry['model']),None)
    if not row and entry.get('started'):
        current=read_json(ROOT/'logs/current_task.json',{})
        recovered=read_json(ROOT/current.get('run_path','')/'result.json',{})
        if recovered and recovered['model']['name']==entry['model'] and recovered.get('task')=='detective' and recovered.get('sensory_track')==text_detective.TRACK and recovered.get('start','')>=entry['started']:row=recovered
    if not row:
        lock=ROOT/'logs/gpu-controller.lock';existing=read_json(lock,{})
        if existing and psutil.pid_exists(existing.get('pid',-1)):return False
        lock.unlink(missing_ok=True)
        try:fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        except FileExistsError:return False
        with os.fdopen(fd,'w') as handle:json.dump({'pid':os.getpid(),'start':now(),'campaign':CAMPAIGN},handle)
        try:
            model=next(m for m in discover() if m['name']==entry['model'])
            entry.update(status='running',started=now(),pid=os.getpid(),limit_seconds=3600);write_json(PLAN,plan)
            print('INITIAL',entry['model'],'written-evidence Detective case_03',flush=True)
            row=attempt(model,entry)
        finally:
            if read_json(lock,{}).get('pid')==os.getpid():lock.unlink(missing_ok=True)
    if row.get('campaign')!=CAMPAIGN:
        row.update(campaign=CAMPAIGN,variant='Written-evidence Detective initial; images unavailable; separate rubric')
        write_json(ROOT/row['run_path']/'result.json',row)
    else:row=read_json(ROOT/row['run_path']/'result.json')
    entry.update(status='done',run_id=row['run_id'],finished=now());write_json(PLAN,plan)
    active_path=ROOT/'results/active_campaign.json';active=read_json(active_path,{})
    if row['run_id'] not in active.setdefault('run_ids',[]):
        active['run_ids'].append(row['run_id']);active.setdefault('entries',[]).append({**entry,'status':'done','missing_written_initial':True})
        active['updated']=now();write_json(active_path,active)
    export();append_result(row,campaign)
    print('INITIAL SAVED',entry['model'],row['run_id'],flush=True)
    return True
