"""Resume a saved user request without resetting its time or model-call budget."""
from benchmark.util import read_json
from benchmark.harness.metrics_collector import rows


def budget(info,cfg):
    checkpoint=info.get('resume_checkpoint')
    if not checkpoint or checkpoint['update_id']!=info.get('current_update_id'):
        return float(cfg['task_timeout_seconds']),int(cfg['max_calls']),None
    return max(0,float(cfg['task_timeout_seconds'])-checkpoint['used_seconds']),max(0,int(cfg['max_calls'])-checkpoint['started_calls']),checkpoint


def saved_messages(path,checkpoint):
    """Recover completed conversation only; an interrupted response is never executed."""
    if not checkpoint:return None
    calls=[r for r in rows(path/'inference_calls.jsonl') if r['start']>=checkpoint['request_created']]
    if not calls:return None
    call=calls[-1];messages=[dict(m) for m in call.get('request_messages',[])]
    if any(m.get('images') for m in messages):return None
    # The next controller reminder uses the remaining budget, not stale time.
    if messages and messages[-1].get('content','').startswith('Controller budget:'):messages.pop()
    messages.append({'role':'assistant','content':call.get('content','')})
    for item in rows(path/'tool_calls.jsonl'):
        if item.get('start','')<call.get('end',''):continue
        if item.get('category')=='invalid_arguments':
            messages.append({'role':'user','content':'Tool protocol error: '+item.get('stderr','')+'. Return valid JSON. Files must be created through tools; prose alone is not a submission.'})
        elif item.get('category') not in ['environment_setup','image_read']:
            messages.append({'role':'user','content':'Saved tool result: '+str({k:item.get(k) for k in ['exit_code','stdout','stderr']})})
    return messages if messages else None


def prior_hardware(info,checkpoint):
    prior=dict(info.get('performance') or {})
    if not checkpoint:return prior
    partial=checkpoint.get('hardware_summary',{})
    for key in ['peak_vram_bytes','peak_ram_bytes','peak_inference_rss_bytes','peak_gpu_temperature_c']:
        prior[key]=max((v for v in [prior.get(key),partial.get(key)] if v is not None),default=None)
    for key in ['samples','estimated_gpu_energy_joules']:
        values=[v for v in [prior.get(key),partial.get(key)] if v is not None]
        prior[key]=sum(values) if values else None
    return prior
