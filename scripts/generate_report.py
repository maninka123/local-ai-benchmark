import _bootstrap,html
from benchmark.util import ROOT,read_json,now,source_hash,write_json
from benchmark.scoring.aggregate_scorer import export
from markdown_it import MarkdownIt
from extensions.improvement_reporting import receipt,section

def main():
    all_records,all_flat=export();protocol=source_hash();campaign=read_json(ROOT/'results'/'active_campaign.json',{});ids=set(campaign.get('run_ids',[]));records=[r for r in all_records if (r['run_id'] in ids if ids else r['protocol_hash']==protocol)];flat=[r for r in all_flat if r['run_id'] in {x['run_id'] for x in records}];discovered=read_json(ROOT/'models'/'discovered.json',{}).get('models',[])
    lines=['# Local capability benchmark — pilot results',f'\nGenerated {now()}. RTX 4080 / i9-13900K / 64 GB RAM. Inspect AI with local Ollama.','\nAutomatic verified points are a lower bound, not a completed intelligence score. Subjective and behavioral rubric items remain pending independent review. Single pilots do not establish statistical reliability.',
        '\n## Coverage',f'\nDiscovered {len(discovered)} models; recorded {len(records)} attempts in the selected campaign/cohort (active protocol `{protocol[:12]}`). {len(all_records)-len(records)} calibration/historical attempts remain preserved separately in master results. DeepSeek-OCR is excluded. Text-only models receive compatible data and coding tasks. Text-only models also receive a separate written-evidence Detective test (images excluded), which does not enter visual rankings. No unsupported modality is scored as zero.',
        '\n| Model | Task / case | Status | Verified points | Pending points | Automatic checks passed | Gen tok/s | Task seconds |', '|---|---|---|---:|---:|---|---:|---:|']
    by_id={r['run_id']:r for r in records}
    for r in flat:
        r={**r,'task':r['task']+(' (text only)' if by_id[r['run_id']].get('sensory_track')=='text_only_detective' else '')}
        speed=f'{r["generation_tps"]:.1f}' if r['generation_tps'] is not None else 'unavailable'
        lines.append(f'| {r["model"]} | {r["task"]} {r["case"] or ""} | {r["status"]} | {r["verified_points"]} | {r["pending_points"]} | {r["complete"]} | {speed} | {r["task_seconds"]:.1f} |')
    if campaign:
        lines+=['\n## One-hour campaign and deadline retries', '\n'+campaign['note'], '\nDifferent task budgets affect completion opportunity; this mixed-budget campaign is not an equal-budget quality ranking. Use the dashboard protocol filter for the one-hour cohort. Original failures and retry artifacts remain separate.', '\n| Model | Task / case | Limit (minutes) | Protocol | Retry of |','|---|---|---:|---|---|']
        for r in records:lines.append(f'| {r["model"]["name"]} | {r["task"]} {r.get("case") or ""} | {r["config"]["benchmark"]["task_timeout_seconds"]/60:g} | {r["protocol_hash"][:12]} | {r.get("retry_of") or "Initial attempt"} |')
    lines+=['\n## Measurement and scoring limits','\nGeneration throughput = sum of actual Ollama eval_count / sum of eval_duration seconds. It includes native thinking when the backend includes it; separate reasoning tokens are unavailable. TTFT is measured to the first content or thinking chunk. First visible token latency is separately logged. Cold calls have load_duration >1 second. RAM/VRAM peaks and GPU power are whole-machine/device observations, not exclusive attribution.',
        '\nA score of zero for missing files is an observed failure. Pending rubric categories are null, never silently zero. A runnable game is not automatically a complete racing game; collisions, NPC behavior, valid laps and visual quality require independent review. Detective timeline references and model hooks are diagnostic only. No candidate grades itself. Manual corrections require an audit entry.',
        '\n## Reproduce', '\nSee README.md for setup, immutable/resumable runs, dashboard and final-repetition commands. Dataset hashes, exact prompts, package versions, per-call request/response logs and Inspect transcripts accompany results.',
        '\n## Artifacts','\n[Dashboard](http://127.0.0.1:8765) · [CSV](master_results.csv) · [JSON](master_results.json) · [Aggregates](aggregates.json)']
    rankings=[]
    for model in discovered:
        group=[r for r in records if r['model']['digest']==model['digest'] and r.get('sensory_track')!='text_only_detective']
        task_scores={}
        for task in ['data_analysis','racing_game']+(['detective'] if model['vision'] else []):
            attempts=[r for r in group if r['task']==task]
            values=[r['scores']['quality_score'] for r in attempts]
            task_scores[task]=sum(values)/len(values) if values and all(v is not None for v in values) else None
        full=all(v is not None for v in task_scores.values())
        weights={'data_analysis':.3333,'racing_game':.3333,'detective':.3334} if model['vision'] else {'data_analysis':.5,'racing_game':.5}
        rankings.append({'model':model['name'],'track':'native multimodal (3 tasks)' if model['vision'] else 'text and coding (2 tasks)',
            'task_scores':task_scores,'quality_score':sum(task_scores[k]*weights[k] for k in weights) if full else None,
            'completion_rate':sum(r['scores']['complete'] for r in group)/len(group) if group else None,'evaluated_attempts':len(group),
            'note':'Separate sensory tracks; null quality means pending/missing rubric evaluations. No opaque quality/speed combined score. Completion rate is the saved automatic flag; full task completion is reviewed separately in Task progress.'})
    write_json(ROOT/'results'/'rankings.json',rankings)
    lines+=['\n## Quality ranking eligibility','\n| Model | Compatible track | Full rubric score | Automatic check pass rate (%) |','|---|---|---:|---:|']
    for r in rankings:lines.append(f'| {r["model"]} | {r["track"]} | {r["quality_score"] if r["quality_score"] is not None else "Pending"} | {round(100*r["completion_rate"],1) if r["completion_rate"] is not None else "Pending"} |')
    written=[r for r in records if r.get('sensory_track')=='text_only_detective']
    if written:
        lines+=['\n## Written-evidence Detective (separate rubric)','Images were not supplied. Compare these results only with this text-only version; full quality remains pending review.','| Model | Verified / pending points | Full quality | Time (min) |','|---|---|---|---:|']
        for r in written:lines.append(f"| {r['model']['name']} | {r['scores']['verified_points']} / {r['scores']['pending_points']} | {r['scores']['quality_score'] if r['scores']['quality_score'] is not None else 'Pending'} | {r['task_seconds']/60:.1f} |")
    improvements=receipt()
    lines.insert(3,section(improvements))
    write_json(ROOT/'results'/'reports'/'improvement_results.json',improvements)
    report='\n'.join(lines);(ROOT/'results'/'benchmark_summary.md').write_text(report,encoding='utf-8')
    reports=ROOT/'results'/'reports';reports.mkdir(exist_ok=True)
    (reports/'benchmark_report.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local capability benchmark</title><style>*{box-sizing:border-box}body{overflow-wrap:anywhere;font:18px/1.6 system-ui;max-width:1500px;margin:40px auto;padding:20px}table{display:block;width:100%;max-width:100%;overflow:auto;border-collapse:collapse}td,th{padding:9px;border:1px solid #ddd;text-align:left;vertical-align:top}a{color:#1262b4}code{overflow-wrap:anywhere}</style>'+MarkdownIt().enable('table').render(report),encoding='utf-8')
    print(f'Report saved: {ROOT / "results" / "benchmark_summary.md"}')
if __name__=='__main__':main()
