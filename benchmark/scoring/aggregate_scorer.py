import sqlite3,json,csv,statistics
from benchmark.util import ROOT,read_json,write_json
from benchmark.harness.metrics_collector import distribution

def export():
    records=[]
    for p in (ROOT/'models').glob('*/*/*/result.json'):
        row=read_json(p)
        if row:
            reviews=p.parent/'manual_reviews.jsonl'
            if reviews.exists():
                audit=json.loads(reviews.read_text(encoding='utf-8').splitlines()[-1])
                row['original_scores']=row['scores'];row['manual_review']=audit
                row['scores']={**row['scores'],'categories':audit['reviewed_categories'],'quality_score':audit['quality_score'],
                    'complete':audit['complete'],'pending_points':0,'review_status':'reviewed'}
            records.append(row)
    records.sort(key=lambda x:x['start'])
    write_json(ROOT/'results'/'master_results.json',records)
    flat=[]
    for r in records:
        m=r['model'];s=r.get('scores',{});v=r.get('performance',{})
        flat.append({'run_id':r['run_id'],'model':m['name'],'digest':m['digest'],'task':r['task'],'case':r.get('case'),'start':r['start'],'status':r['status'],
            'repetition':r['repetition'],'pilot':r['pilot'],'vision':m['vision'],'architecture':m['architecture'],'quantization':m['quantization'],'parameters':m['parameters'],
            'quality_score':s.get('quality_score'),'verified_points':s.get('verified_points'),'pending_points':s.get('pending_points'),
            'complete':s.get('complete',False),'generation_tps':v.get('generation_tps'),'prompt_tps':v.get('prompt_tps'),'ttft_seconds':v.get('ttft',{}).get('median'),
            'task_seconds':r.get('task_seconds'),'peak_vram_bytes':v.get('peak_vram_bytes'),'peak_ram_bytes':v.get('peak_ram_bytes'),
            'tool_calls':v.get('tool_calls'),'tool_failures':v.get('tool_failures'),'inference_calls':v.get('inference_calls'),'output_tokens':v.get('output_tokens'),
            'residency':r.get('residency'),'run_path':r['run_path'],'protocol_hash':r.get('protocol_hash')})
    resultdir=ROOT/'results';resultdir.mkdir(exist_ok=True)
    with (resultdir/'master_results.csv').open('w',newline='',encoding='utf-8') as f:
        if flat:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
    with sqlite3.connect(resultdir/'benchmark.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, model TEXT, task TEXT, case_id TEXT, status TEXT, result_json TEXT NOT NULL)')
        for r in records:db.execute('INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?)',(r['run_id'],r['model']['name'],r['task'],r.get('case'),r['status'],json.dumps(r)))
        db.execute('CREATE TABLE IF NOT EXISTS reviews (review_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, timestamp TEXT NOT NULL, reviewer TEXT NOT NULL, original_json TEXT NOT NULL, corrected_json TEXT NOT NULL, reason TEXT NOT NULL)')
    grouped=[]
    for key in sorted(set((r['model']['name'],r['task'],r['protocol_hash'],r['pilot']) for r in records)):
        group=[r for r in records if (r['model']['name'],r['task'],r['protocol_hash'],r['pilot'])==key]
        seconds=sum(r['performance'].get('generation_seconds',0) for r in group);tokens=sum(r['performance'].get('output_tokens',0) for r in group)
        grouped.append({'model':key[0],'task':key[1],'protocol_hash':key[2],'pilot':key[3],'attempts':len(group),
            'completion_rate':sum(r['scores'].get('complete',False) for r in group)/len(group),
            'weighted_generation_tps':tokens/seconds if seconds else None,'task_time':distribution([r['task_seconds'] for r in group]),
            'verified_points':distribution([r['scores'].get('verified_points') for r in group]),
            'quality_score':distribution([r['scores'].get('quality_score') for r in group])})
    write_json(resultdir/'aggregates.json',grouped)
    return records,flat
