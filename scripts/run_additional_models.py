"""Append four new models to the saved campaign, with three task types each."""
import _bootstrap,argparse,os,sys,json,time,psutil,httpx,hashlib
from unittest.mock import patch
from benchmark.util import ROOT,config,source_hash,read_json,write_json,now,artifact_files
from benchmark.harness.model_discovery import discover
from benchmark.harness import runner
from benchmark.scoring.aggregate_scorer import export
from extensions import text_detective,gpt_oss_transport,windows_io
from run_extended_pilot import timed_out

MODELS=['gpt-oss:20b','qwen3-coder-next:q4_K_M','qwen3-next:80b-a3b-thinking-q4_K_M','qwen3-vl:30b-a3b-instruct']
VISION_MODELS={'qwen3-vl:30b-a3b-instruct'}

def protocol(name,track):
    base=text_detective.protocol() if track==text_detective.TRACK else source_hash()
    return gpt_oss_transport.protocol(base) if name.startswith('gpt-oss:') else base

def plan(campaign,models,third):
    entries=campaign.setdefault('entries',[])
    for name in models:
        slots=[('data_analysis',None,1,'text_and_tools'),('racing_game',None,1,'text_and_tools')]
        if name in VISION_MODELS:slots+=[('detective',case,1,'native_multimodal') for case in ['case_01','case_02','case_03']]
        else:slots+=[('detective','case_03',1,text_detective.TRACK)] if third=='text-detective' else [('data_analysis',None,2,'text_and_tools')]
        for task,case,rep,track in slots:
            if any(e['model']==name and e['task']==task and e.get('case')==case and e.get('repetition',1)==rep and not e.get('retry') for e in entries):continue
            entries.append({'model':name,'digest':None,'task':task,'case':case,'repetition':rep,'sensory_track':track,'retry':False,'status':'pending','run_id':None,'additional_models':True})
    return campaign

def attempt_inner(model,entry):
    if entry['sensory_track']==text_detective.TRACK:
        original_workspace=runner.create_workspace
        with patch.object(runner,'create_workspace',lambda m,t,c:text_detective.workspace(original_workspace,m,t,c)),patch.object(runner,'make_task',text_detective.make_task),patch.dict(runner.SCORERS,{'detective':text_detective}):
            row=runner.run_attempt(model,entry['task'],entry['case'],entry['repetition'],True)
        row.update(sensory_track=text_detective.TRACK,protocol_hash=text_detective.protocol(),variant='Written-evidence Detective; separate from native visual tests')
    else:row=runner.run_attempt(model,entry['task'],entry['case'],entry['repetition'],True)
    row.update(campaign='additional_three_models',retry_of=entry.get('retry_of'),retry_kind=entry.get('retry_kind'),protocol_hash=protocol(model['name'],entry['sensory_track']))
    if model['name'].startswith('gpt-oss:'):row['transport']='Native sandbox action bridge; same sandbox actions, separate compatibility protocol'
    write_json(ROOT/row['run_path']/'result.json',row)
    return row

def attempt(model,entry):
    with patch.object(runner,'OllamaAdapter',gpt_oss_transport.adapter):return attempt_inner(model,entry)

def recover(campaign,history):
    for index,entry in list(enumerate(campaign['entries'])):
        previous=next((r for r in history if r['run_id']==entry.get('run_id')),None)
        if entry.get('additional_models') and entry['model'].startswith('gpt-oss:') and previous and previous.get('status')=='failed' and previous.get('protocol_hash')!=protocol(entry['model'],entry.get('sensory_track','text_and_tools')):
            if not any(e.get('retry_of')==previous['run_id'] for e in campaign['entries']):
                campaign['entries'].insert(index+1,{**entry,'status':'pending','run_id':None,'retry':True,'retry_kind':'compatibility_recovery','retry_of':previous['run_id']})
    return campaign

def recover_save_error(campaign):
    current=read_json(ROOT/'logs/current_task.json',{})
    run=(ROOT/current.get('run_path','')).resolve()
    if not run.is_relative_to((ROOT/'models').resolve()):return
    row=read_json(run/'result.json',{})
    if row.get('status')!='failed' or 'PermissionError' not in str(row.get('error')):return
    for index,entry in enumerate(campaign['entries']):
        if entry.get('additional_models') and entry['status']=='running' and entry['model']==row['model']['name'] and entry['task']==row['task'] and entry.get('case')==row.get('case'):
            entry.update(status='done',run_id=row['run_id'])
            if row['run_id'] not in campaign['run_ids']:campaign['run_ids'].append(row['run_id'])
            if not any(e.get('retry_of')==row['run_id'] for e in campaign['entries']):
                campaign['entries'].insert(index+1,{**entry,'status':'pending','run_id':None,'retry':True,'retry_kind':'infrastructure_recovery','retry_of':row['run_id']})
            # The failed result file remains byte-for-byte unchanged.
            return

def main(argv=None):
    with windows_io.atomic_replacements(ROOT):return run_campaign(argv)

def run_campaign(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--third',choices=['text-detective','repeat-data'],default='text-detective');parser.add_argument('--wait-downloads',action='store_true');args=parser.parse_args(argv)
    if config()['benchmark']['task_timeout_seconds']!=3600:raise SystemExit('Expected the saved one-hour limit.')
    if not read_json(ROOT/'results/setup_validation.json',{}).get('all_passed'):raise SystemExit('Sandbox setup validation must pass.')
    path=ROOT/'results/active_campaign.json';campaign=read_json(path,{})
    if campaign.get('status')=='running' and read_json(ROOT/'logs/gpu-controller.lock',{}):raise SystemExit('A benchmark is already running.')
    original_ids=set(campaign.get('run_ids',[]));before={r['run_id']:hashlib.sha256((ROOT/r['run_path']/'result.json').read_bytes()).hexdigest() for r in read_json(ROOT/'results/master_results.json',[]) if r['run_id'] in original_ids}
    if not any(e.get('additional_models') for e in campaign.get('entries',[])):write_json(ROOT/'results/campaign_archives'/('before-three-models-'+now().replace(':','')+'.json'),campaign)
    campaign.setdefault('run_ids',[]);recover_save_error(campaign)
    plan(campaign,MODELS,args.third);recover(campaign,read_json(ROOT/'results/master_results.json',[]))
    campaign.pop('stopped_at',None);campaign.pop('stop_reason',None);campaign.pop('finished',None)
    campaign.update(name='Initial benchmark + four additional models',status='waiting_downloads',protocol_hash=source_hash(),limit_seconds=3600,
        note='Previous initial results and retries retained. Three added text models run Data analysis, Racing game and written-evidence Detective (case 03, images excluded). Qwen3-VL runs Data analysis, Racing game and all three native visual Detective cases. Each attempt has a 60-minute limit. GPT-OSS uses a separately recorded native sandbox transport; the earlier failure is retained. The written and visual Detective rubrics are separate.' if args.third=='text-detective' else 'Previous results retained. Three added models run Data analysis, Racing game and a second Data analysis attempt, each with a 60-minute limit.')
    write_json(path,campaign)
    while True:
        models=discover();by_name={m['name']:m for m in models};missing=[n for n in MODELS if n not in by_name]
        downloading=read_json(ROOT.parent/'download_status.json',{}).get('status')=='downloading'
        if not missing and not downloading:break
        if not args.wait_downloads:raise SystemExit('Models not ready: '+str(missing))
        print('WAIT downloads:',missing,flush=True);time.sleep(15)
    lock=ROOT/'logs/gpu-controller.lock';lock.parent.mkdir(exist_ok=True)
    while True:
        existing=read_json(lock,{})
        if existing and psutil.pid_exists(existing.get('pid',-1)):print('WAIT current GPU operation',flush=True);time.sleep(5);continue
        lock.unlink(missing_ok=True)
        try:fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL);break
        except FileExistsError:time.sleep(1)
    with os.fdopen(fd,'w') as f:json.dump({'pid':os.getpid(),'start':now(),'campaign':'additional_three_models'},f)
    try:
        campaign.update(status='running');campaign.pop('finished',None);write_json(path,campaign)
        export();history=read_json(ROOT/'results/master_results.json',[])
        index=0
        while index<len(campaign['entries']):
            entry=campaign['entries'][index];index+=1
            if not entry.get('additional_models') or entry['status']=='done':continue
            model=by_name[entry['model']];entry['digest']=model['digest']
            previous=next((r for r in reversed(history) if r['model']['digest']==model['digest'] and r['task']==entry['task'] and r.get('case')==entry['case'] and r['repetition']==entry['repetition'] and r.get('sensory_track')==entry['sensory_track'] and r.get('pilot') and r.get('protocol_hash')==protocol(model['name'],entry['sensory_track']) and (not entry.get('retry') or r.get('retry_of')==entry.get('retry_of'))),None)
            if previous:row=previous
            else:
                entry['status']='running';campaign['current_index']=index-1;write_json(path,campaign)
                print(f"START {entry['model']} {entry['task']} {entry['case'] or ''} rep={entry['repetition']} limit=3600s",flush=True)
                row=attempt(model,entry);history.append(row)
            entry.update(status='done',run_id=row['run_id'])
            if row['run_id'] not in campaign['run_ids']:campaign['run_ids'].append(row['run_id'])
            if timed_out(row) and (not entry['retry'] or entry.get('retry_kind')=='compatibility_recovery') and not any(e.get('retry_of')==row['run_id'] for e in campaign['entries']):campaign['entries'].append({**entry,'status':'pending','run_id':None,'retry':True,'retry_kind':'deadline','retry_of':row['run_id']})
            export();write_json(path,campaign)
        assert all(hashlib.sha256((ROOT/next(r['run_path'] for r in history if r['run_id']==run_id)/'result.json').read_bytes()).hexdigest()==digest for run_id,digest in before.items())
        campaign.update(status='complete',finished=now());campaign.pop('current_index',None);write_json(path,campaign)
        from generate_report import main as report
        report();added=[r for r in history if r.get('campaign')=='additional_three_models']
        checks=[]
        for row in added:
            run=ROOT/row['run_path']
            from benchmark.harness.metrics_collector import collect
            expected=collect(run)['generation_tps'];actual=row['performance']['generation_tps']
            checks.append({'run_id':row['run_id'],'model':row['model']['name'],'task':row['task'],'sensory_track':row['sensory_track'],'original_limit_seconds':row['config']['benchmark']['task_timeout_seconds'],
                'weighted_tps_correct':expected==actual,'files_saved':all((run/f).is_file() for f in ['result.json','scores.json','performance.json','hardware_metrics.csv']),
                'images_supplied':any(c.get('image_count',0) for c in __import__('benchmark.harness.metrics_collector',fromlist=['rows']).rows(run/'inference_calls.jsonl'))})
        write_json(ROOT/'results/additional_models_validation.json',{'timestamp':now(),'original_results_unchanged':True,'model_count':len(MODELS),'attempts':len(added),'checks':checks})
        print('COMPLETE: additional model results and validation saved.',flush=True)
    except BaseException:
        campaign['status']='interrupted';write_json(path,campaign);raise
    finally:
        if read_json(lock,{}).get('pid')==os.getpid():lock.unlink(missing_ok=True)

if __name__=='__main__':main()
