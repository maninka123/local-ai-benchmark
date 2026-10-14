"""Refresh reports on saved results and perform a final artifact/metrics audit."""
import _bootstrap,time,psutil
from benchmark.util import ROOT,read_json,write_json,now,source_hash
from generate_report import main as report
from benchmark.harness.metrics_collector import rows

path=ROOT/'results'/'master_results.json';last=None;started=now();protocol=source_hash()
while True:
    lock=read_json(ROOT/'logs'/'gpu-controller.lock',{})
    stamp=path.stat().st_mtime_ns if path.exists() else None
    if stamp!=last:
        report();last=path.stat().st_mtime_ns if path.exists() else None
    if not lock or not psutil.pid_exists(lock.get('pid',-1)):break
    time.sleep(10)
report()
campaign=read_json(ROOT/'results'/'active_campaign.json',{});ids=set(campaign.get('run_ids',[]))
records=[r for r in read_json(path,[]) if (r['run_id'] in ids if ids else r.get('protocol_hash')==protocol)];checks=[]
for r in records:
    run=ROOT/r['run_path'];calls=rows(run/'inference_calls.jsonl');seconds=sum((c.get('eval_duration_ns') or 0)/1e9 for c in calls);tokens=sum(c.get('output_tokens') or 0 for c in calls)
    expected=tokens/seconds if seconds else None;actual=r['performance'].get('generation_tps')
    checks.append({'run_id':r['run_id'],'model':r['model']['name'],'task':r['task'],'case':r.get('case'),
        'weighted_token_speed_correct':(expected is None and actual is None) or (expected is not None and actual is not None and abs(expected-actual)<1e-8),
        'identity_present':(run/'identity.json').exists(),'scores_present':(run/'scores.json').exists(),'hardware_present':(run/'hardware_metrics.csv').exists(),
        'image_count_logged':any(c.get('image_count',0)>0 for c in calls) if r['task']=='detective' else None})
write_json(ROOT/'results'/'execution_validation.json',{'timestamp':now(),'protocol_hash':protocol,'observer_start':started,'attempts':len(records),'expected_unique_task_slots':36,'planned_attempts_including_retries':len(campaign.get('entries',[])) if campaign else 36,
    'unique_models_evaluated':sorted({r['model']['name'] for r in records}),'checks':checks,'complete_coverage':len({(r['model']['digest'],r['task'],r.get('case')) for r in records})==36,
    'task_wall_seconds_sum':sum(r['task_seconds'] for r in records),'note':'Task times use monotonic clocks. Sum excludes controller time between attempts. Unavailable subjective/behavior scores remain null.'})
print(f'Final audit: {len(records)} current-protocol attempts, {len(set(r["model"]["name"] for r in records))} models.',flush=True)
