import json,statistics
from benchmark.util import read_json

def rows(path):
    if not path.exists():return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def distribution(values):
    values=[v for v in values if v is not None]
    return {'count':len(values),'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None,
        'min':min(values) if values else None,'max':max(values) if values else None,'std':statistics.stdev(values) if len(values)>1 else None}

def collect(run):
    calls=rows(run/'inference_calls.jsonl');tools=rows(run/'tool_calls.jsonl')
    duration=sum((c.get('eval_duration_ns') or 0)/1e9 for c in calls);pd=sum((c.get('prompt_eval_duration_ns') or 0)/1e9 for c in calls)
    result={'inference_calls':len(calls),'tool_calls':len(tools),'inference_failures':sum(not c['success'] for c in calls),
        'tool_failures':sum(c.get('exit_code',0)!=0 for c in tools),'output_tokens':sum(c.get('output_tokens') or 0 for c in calls),
        'input_tokens':sum(c.get('input_tokens') or 0 for c in calls),'generation_seconds':duration,'prompt_seconds':pd,
        'inference_wall_seconds':sum(c['wall_seconds'] for c in calls),'load_seconds':sum((c.get('load_duration_ns') or 0)/1e9 for c in calls),
        'ttft':distribution([c.get('ttft_seconds') for c in calls]),'generation_tps_distribution':distribution([c.get('generation_tokens_per_second') for c in calls]),
        'cold_calls':[c['call'] for c in calls if (c.get('load_duration_ns') or 0)>1e9],
        'warm_calls':[c['call'] for c in calls if c.get('load_duration_ns') is not None and c['load_duration_ns']<=1e9],
        'reasoning_token_count':None,'reasoning_note':'Ollama exposes thinking text but not its separate token count.',
        'time_categories_overlap':False,'category_note':'Inference wall includes load/prompt/generation; do not add those components to inference wall. Hardware sampling overlaps all categories.'}
    result['generation_tps']=result['output_tokens']/duration if duration else None
    result['prompt_tps']=result['input_tokens']/pd if pd else None
    result['tool_categories']={cat:{'calls':sum(t['category']==cat for t in tools),'seconds':sum(t['duration_seconds'] for t in tools if t['category']==cat),
        'failures':sum(t['category']==cat and t['exit_code']!=0 for t in tools)} for cat in set(t['category'] for t in tools)}
    return result
