"""Continue the pilot with a one-hour deadline; retry timeouts once at the end."""
import _bootstrap,argparse,os,psutil,json,subprocess,sys
from benchmark.util import ROOT,config,source_hash,read_json,write_json,now
from benchmark.harness.model_discovery import discover
from benchmark.harness.runner import run_attempt
from benchmark.scoring.aggregate_scorer import export

def timed_out(row):
    return 'deadline exceeded' in str(row.get('error','')).lower() or row.get('performance',{}).get('stop_reason')=='time_budget'

def key(row):return (row['model']['digest'],row['task'],row.get('case'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True);args=parser.parse_args()
    cfg=config()['benchmark'];protocol=source_hash()
    if cfg['task_timeout_seconds']!=3600:raise SystemExit('This campaign requires the configured one-hour deadline.')
    if not read_json(ROOT/'results'/'setup_validation.json',{}).get('all_passed'):raise SystemExit('Sandbox setup validation must pass first.')
    models=discover();lookup={m['digest']:m for m in models};lock=ROOT/'logs'/'gpu-controller.lock'
    existing=read_json(lock,{})
    if existing and psutil.pid_exists(existing.get('pid',-1)):raise SystemExit('Another GPU controller is active.')
    lock.unlink(missing_ok=True)
    with os.fdopen(os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL),'w') as f:json.dump({'pid':os.getpid(),'start':now(),'campaign':'one_hour_pilot'},f)
    path=ROOT/'results'/'active_campaign.json';campaign=read_json(path,{})
    try:
        if not campaign or campaign.get('baseline_protocol')!=args.baseline:
            history=[r for r in read_json(ROOT/'results'/'master_results.json',[]) if r.get('protocol_hash')==args.baseline and r.get('pilot') and r.get('repetition')==1]
            entries=[];retries=[]
            for model in models:
                slots=[('data_analysis',None),('racing_game',None)]+([('detective',c) for c in ['case_01','case_02','case_03']] if model['vision'] else [])
                for task,case in slots:
                    prior=next((r for r in reversed(history) if key(r)==(model['digest'],task,case)),None)
                    entry={'digest':model['digest'],'model':model['name'],'task':task,'case':case,'retry':False,'status':'done' if prior else 'pending','run_id':prior['run_id'] if prior else None}
                    entries.append(entry)
                    if prior and timed_out(prior):retries.append({**entry,'retry':True,'status':'pending','run_id':None,'retry_of':prior['run_id']})
            campaign={'name':'One-hour pilot','created':now(),'baseline_protocol':args.baseline,'protocol_hash':protocol,'limit_seconds':3600,'entries':entries+retries,'run_ids':[r['run_id'] for r in history],'status':'running',
                'note':'Completed 30-minute attempts retained. Remaining attempts and one timeout retry per slot use 60 minutes; retries run after the initial queue. Budgets are recorded per attempt.'}
        elif campaign['protocol_hash']!=protocol:raise RuntimeError('Campaign source/config changed; inspect the recorded protocol before resuming.')
        campaign['status']='running';write_json(path,campaign)
        # One report observer follows this controller, including the final audit.
        if os.environ.get('LLMB_START_OBSERVER')=='1':
            subprocess.Popen([sys.executable,str(ROOT/'scripts'/'watch_results.py')],cwd=ROOT,
                stdout=(ROOT/'logs'/'watch-one-hour.stdout.log').open('w'),stderr=(ROOT/'logs'/'watch-one-hour.stderr.log').open('w'),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        index=0
        while index<len(campaign['entries']):
            entry=campaign['entries'][index];index+=1
            if entry['status']=='done':continue
            entry['status']='running';campaign['current_index']=index-1;write_json(path,campaign)
            print(f"START {'RETRY ' if entry['retry'] else ''}{entry['model']} {entry['task']} {entry['case'] or ''} limit=3600s",flush=True)
            row=run_attempt(lookup[entry['digest']],entry['task'],entry['case'],1,True)
            row['campaign']='one_hour_pilot';row['retry_of']=entry.get('retry_of');write_json(ROOT/row['run_path']/'result.json',row)
            entry.update(status='done',run_id=row['run_id']);campaign['run_ids'].append(row['run_id'])
            if timed_out(row) and not entry['retry']:
                campaign['entries'].append({**entry,'retry':True,'status':'pending','run_id':None,'retry_of':row['run_id']})
            export();write_json(path,campaign)
        campaign['status']='complete';campaign['finished']=now();campaign.pop('current_index',None);write_json(path,campaign)
        from generate_report import main as report
        report()
    except BaseException:
        if campaign:campaign['status']='interrupted';write_json(path,campaign)
        raise
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':main()
