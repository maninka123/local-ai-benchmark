"""Validate separate review receipts and export a readable report."""
import _bootstrap
import hashlib,json
import os
from pathlib import Path
from collections import Counter
from benchmark.util import ROOT,read_json,write_json,now
from dashboard.backend.judging import judging

def accessible(name):
    path=ROOT/name
    return Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path

def main():
    data=judging();rows=data['rows']
    campaign=read_json(ROOT/'results/improvement_campaign/pass_2/campaign.json',{})
    expected={e['run_id'] for e in campaign['entries']}
    assert len(rows)==53 and {r['run_id'] for r in rows}==expected
    assert len({r['run_id'] for r in rows})==len(rows)
    for row in rows:
        assert [a['number'] for a in row['attempts']]==[1,2,3]
        for a in row['attempts']:
            assert a['evidence_files'] and all(accessible(p).exists() for p in a['evidence_files'])
            assert all('/repairs/' not in p.replace('\\','/') for p in a['evidence_files'])
    frozen=read_json(ROOT/'results/improvement_campaign/pass_2/preserved_fingerprints.json',{})
    changed=[p for p,digest in frozen.items() if not accessible(p).is_file() or hashlib.sha256(accessible(p).read_bytes()).hexdigest()!=digest]
    assert not changed,changed
    write_json(ROOT/'results/judged_scores/reviewed_results.json',data)
    receipt={'timestamp':now(),'results':len(rows),'attempt_judgments':sum(len(r['attempts']) for r in rows),'coverage':dict(Counter(r['task'] for r in rows)),'preserved_files_checked':len(frozen),'changed_paths':changed,'score_policy':data['policy'],'latest_score_range':[min(r['final']['score'] for r in rows),max(r['final']['score'] for r in rows)],'latest_distinct_scores':len({r['final']['score'] for r in rows})}
    write_json(ROOT/'results/judged_scores/validation.json',receipt)
    lines=['# Local model output reviews','',data['policy']['description'],'',data['policy']['exclusions'],'',data['policy']['aggregation'],'','All scores are AI rubric judgments. Output quality and the attempt-adjusted review score are shown separately. Equal outputs can tie; variation is never forced.','','## Latest task results','','| Model | Task / track | Review score | Raw quality | Completed |','|---|---|---:|---:|---:|']
    for a in sorted(data['aggregates'],key=lambda a:(a['task'],-a['score'])):
        lines.append(f"| {a['model']} | {a['task']} / {a['sensory_track']} | {a['score']:.1f} | {a['raw_score']:.1f} | {a['completed']}/{a['cases']} |")
    for r in rows:
        lines.extend(['',f"## {r['model']} · {r['task']} · {r.get('case') or ''}",'',f"Run: `{r['run_id']}`"])
        for a in r['attempts']:
            lines.extend(['',f"### Attempt {a['number']} — {'Complete' if a['completed'] else 'Incomplete'}",'',(f"Final score: **{a['score']:.1f}/100**" if a['is_final'] else 'Earlier attempt: no score awarded.'),'',a['summary'],'','| Criterion | Points | Reason |','|---|---:|---|'])
            for c in a['criteria']:lines.append(f"| {c['name']} | {c['points']:.1f}/{c['max_points']} | {c['reason'].replace('|','/')} |")
            lines.extend(['','Review limits:']+[f'- {x}' for x in a.get('limitations',[])]+['','Saved evidence:']+[f'- `{x}`' for x in a['evidence_files']])
    (ROOT/'results/judged_scores/review_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
