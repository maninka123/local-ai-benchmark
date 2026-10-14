import _bootstrap,argparse,os,fnmatch,psutil,json,sys
from pathlib import Path
from benchmark.util import ROOT,config,source_hash,read_json,write_json,now
from benchmark.harness.model_discovery import discover
from benchmark.harness.runner import run_attempt
from benchmark.scoring.aggregate_scorer import export

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--list-models',action='store_true');p.add_argument('--model',action='append')
    p.add_argument('--task',choices=['data_analysis','racing_game','detective']);p.add_argument('--case',choices=['case_01','case_02','case_03'])
    p.add_argument('--pilot',action='store_true');p.add_argument('--repetitions',type=int,default=1);p.add_argument('--retry-failed',action='store_true');p.add_argument('--force',action='store_true')
    args=p.parse_args(argv);models=discover()
    if args.list_models:
        print('\n'.join(f'{m["name"]} | {m["digest"][:12]} | {m["architecture"]} | {m["quantization"]} | vision={m["vision"]} tools={m["tools"]}' for m in models));return
    if args.model:
        selected=[m for m in models if m['name'] in args.model]
        if len(selected)!=len(set(args.model)):p.error('Model not installed or excluded; use --list-models')
        models=selected
    if args.repetitions<1:p.error('Repetitions must be positive')
    pilot=args.pilot or args.repetitions==1
    protocol=source_hash()
    if args.repetitions>1:
        approval=read_json(ROOT/'results'/'pilot_review.json',{})
        if approval.get('protocol_hash')!=protocol:p.error('Inspect pilot results first, then run scripts/review_pilot.py --acknowledge --notes "...". This gate implements the requested pilot-first protocol.')
    validation=read_json(ROOT/'results'/'setup_validation.json',{})
    if not validation.get('all_passed'):p.error('Run scripts/setup.py successfully first')
    lock=ROOT/'logs'/'gpu-controller.lock';lock.parent.mkdir(exist_ok=True)
    if lock.exists():
        existing=read_json(lock,{})
        if psutil.pid_exists(existing.get('pid',-1)):p.error('A benchmark controller is already running; shared GPU runs must be sequential.')
        lock.unlink()
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    with os.fdopen(fd,'w') as f:json.dump({'pid':os.getpid(),'start':now()},f)
    try:
        history=read_json(ROOT/'results'/'master_results.json',[])
        tasks=[args.task] if args.task else [k for k,v in config()['benchmark']['tasks'].items() if v]
        for model in models:
            for task in tasks:
                if task=='detective' and not model['vision']:
                    print(f'SKIP {model["name"]} detective: unsupported native image input (excluded from multimodal ranking)',flush=True);continue
                cases=[args.case] if task=='detective' and args.case else ['case_01','case_02','case_03'] if task=='detective' else [None]
                for rep in range(1,args.repetitions+1):
                    for case in cases:
                        previous=[r for r in history if r['model']['digest']==model['digest'] and r['task']==task and r.get('case')==case and r['repetition']==rep and r['pilot']==pilot and r.get('protocol_hash')==protocol]
                        if previous and not args.force and not (args.retry_failed and previous[-1]['status']=='failed'):
                            print(f'RESUME skip {model["name"]} {task} {case or ""} rep={rep}',flush=True);continue
                        print(f'START {model["name"]} {task} {case or ""} rep={rep}',flush=True)
                        result=run_attempt(model,task,case,rep,pilot);history.append(result);export()
        from generate_report import main as report
        report()
    finally:
        lock.unlink(missing_ok=True)
if __name__=='__main__':main()
