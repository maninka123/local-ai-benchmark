"""Read-only, source-backed documentation of separate improvement rounds."""
import hashlib,json
from pathlib import Path
from urllib.parse import quote
from benchmark.util import ROOT, read_json, now
from extensions.completion_reviews import normalized


def receipt():
    base = ROOT / 'results/improvement_campaign'
    rounds = []
    sources = []
    for number, folder in [(1, base), (2, base / 'pass_2')]:
        path = folder / 'campaign.json'
        raw=path.read_bytes() if path.is_file() else b'{}'
        campaign = json.loads(raw)
        if not campaign:
            continue
        sources.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest(), 'updated': campaign.get('updated')})
        review_map = {r['run_id']: normalized(r) for task in ['data', 'racing', 'detective'] for r in read_json(folder / (task + '_after_reviews.json'), [])}
        entries = []
        for saved in campaign['entries']:
            entry = dict(saved)
            review = review_map.get(entry['run_id'])
            snapshot = (entry.get('evaluation') or {}).get('snapshot_path', '').replace('\\', '/').rstrip('/')
            if review and review.get('update_id') == entry.get('update_id') and snapshot and any(str(p).replace('\\', '/').startswith(snapshot + '/') for p in review['evidence_files']):
                entry['final_review'] = review
            entries.append(entry)
        rounds.append({'round': number, 'status': campaign['status'], 'created': campaign['created'], 'finished': campaign.get('finished'), 'updated': campaign.get('updated'), 'entries': entries,
                       'evaluated': sum(bool(e.get('evaluation')) for e in entries),
                       'reviewed': sum(isinstance((e.get('final_review') or {}).get('completed'), bool) for e in entries),
                       'completed': sum((e.get('final_review') or {}).get('completed') is True for e in entries),
                       'audit': read_json(folder / 'execution_validation.json', {})})
    return {'generated_at': now(), 'rounds': rounds, 'sources': sources,
            'definitions': {'verified_points': 'Automatically verified rubric points out of 100; a lower bound, not the full quality score.',
                            'pending_points': 'Rubric points awaiting independent manual rating; missing values are not zero.',
                            'completed': 'Independent output review confirms all task requirements. Build success or model finish alone is insufficient.',
                            'stage_minutes': 'Saved prompt elapsed seconds plus its matching evaluation seconds, divided by 60.',
                            'total_minutes': 'Initial task seconds plus all saved further generation and evaluation seconds. Includes earlier manual/setup prompts when present.'}}


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def score(scores):
    if not scores:
        return 'Not evaluated'
    verified = scores.get('verified_points')
    pending = scores.get('pending_points')
    return f'{verified:.1f} verified / {pending:.1f} pending' if isinstance(verified, (int, float)) and isinstance(pending, (int, float)) else 'Unavailable'

def stage_status(entry,number):
    if entry['status']=='incomplete_after_first_pass':return f'Incomplete after improvement {number}'
    if entry['status']=='completed_first_pass':return f'Completed after improvement {number}'
    return entry['status'].replace('_',' ')


def section(data=None):
    data = data or receipt()
    if not data['rounds']:
        return ''
    initial = {r['run_id']: r for r in read_json(ROOT / 'results/master_results.json', [])}
    by_round = {r['round']: {e['run_id']: e for e in r['entries']} for r in data['rounds']}
    latest = data['rounds'][-1]
    lines = ['## Initial results and further improvements',
             'Each improvement uses one outcome-focused prompt for each unfinished result, with a 60-minute limit. Initial results and earlier evaluated snapshots stay saved. Improvement 2 is the third **benchmark** prompt; earlier manual or setup requests can also exist.',
             '| Stage | Evaluated | Independently reviewed | Fully completed | Status |', '|---|---:|---:|---:|---|']
    for stage in data['rounds']:
        lines.append(f"| Improvement {stage['round']} | {stage['evaluated']} / {len(stage['entries'])} | {stage['reviewed']} / {len(stage['entries'])} | {stage['completed']} | {cell(stage['status'].replace('_', ' '))} |")
    lines += [f"Latest stage: **{latest['evaluated']} of {len(latest['entries'])} evaluated, {latest['reviewed']} reviewed, {latest['completed']} fully completed**. Unreviewed work is not claimed complete.",
              'Verified and pending points are shown separately below. They are not a final intelligence ranking. Written-evidence Detective and visual Detective use separate inputs and rubrics.',
              '| Model / task | Initial points | Improvement 1 points | Improvement 2 points | Latest review |', '|---|---|---|---|---|']
    ids = list(dict.fromkeys(e['run_id'] for stage in data['rounds'] for e in stage['entries']))
    for run_id in ids:
        baseline = initial.get(run_id, {})
        stages = [by_round.get(n, {}).get(run_id) for n in [1, 2]]
        entry = next(e for e in reversed(stages) if e)
        review = entry.get('final_review') or {}
        label = f"{entry['model']} / {entry['task'].replace('_', ' ')} {entry.get('case') or ''}"
        if entry.get('sensory_track') == 'text_only_detective':
            label += ' (written evidence only)'
        verdict = 'Completed' if review.get('completed') is True else 'Incomplete' if review.get('completed') is False else 'Review pending'
        lines.append('| ' + ' | '.join([cell(label), score(baseline.get('original_scores',baseline.get('scores'))), *[score((s.get('evaluation') or {}).get('scores')) if s else 'Not scheduled' for s in stages], verdict]) + ' |')
    lines += ['### Per-result evidence, timing and remaining work', 'Elapsed time includes model and tool work. Throughput measures token generation separately. A failed model load is an execution limit, not evidence of poor reasoning.']
    for run_id in ids:
        baseline = initial.get(run_id, {})
        stages = [by_round.get(n, {}).get(run_id) for n in [1, 2]]
        entry = next(e for e in reversed(stages) if e)
        info = read_json(Path(entry['further_folder']).parent / 'revision.json', {}) if entry.get('further_folder') else {}
        if not info:
            first = stages[0]
            if first and first.get('further_folder'): info = read_json(Path(first['further_folder']).parent / 'revision.json', {})
        title = f"{entry['model']} · {entry['task'].replace('_', ' ')} {entry.get('case') or ''}"
        lines += ['#### ' + title, f"[Open this model's work in the dashboard](http://127.0.0.1:8765/?run_id={quote(run_id)}). Initial time: {baseline.get('task_seconds', 0)/60:.1f} min."]
        total = baseline.get('task_seconds', 0) + info.get('generation_seconds', 0) + sum(e.get('seconds', 0) for e in info.get('evaluations', []))
        lines.append(f"Saved total time so far: **{total/60:.1f} min**, including all earlier prompts and evaluations. A running operation's unsaved elapsed time is not included here.")
        for number, stage in enumerate(stages, 1):
            if not stage: continue
            prompt = next((p for p in info.get('prompts', []) if p.get('update_id') == stage.get('update_id')), {})
            evaluation = stage.get('evaluation') or {}
            perf = prompt.get('performance') or {}
            elapsed = prompt.get('seconds', stage.get('seconds'))
            duration = f'{(elapsed + evaluation.get("seconds", 0))/60:.1f} min' if isinstance(elapsed, (int, float)) else 'In progress / not yet measured'
            if stage['status'] in ['awaiting_review','ready','running','evaluating']:
                duration='Final time pending; see live dashboard progress'
            lines += [f"**Improvement {number}:** {cell(stage_status(stage,number))}. Time: {duration}. {score(evaluation.get('scores'))}."]
            if perf:
                speed = perf.get('generation_tps')
                lines.append(f"Input tokens: {perf.get('input_tokens', 'unavailable')}; output tokens: {perf.get('output_tokens', 'unavailable')}; model calls: {perf.get('inference_calls', 'unavailable')}; tool calls: {perf.get('tool_calls', 'unavailable')}; output speed: {f'{speed:.1f} tokens/s' if isinstance(speed, (int, float)) else 'unavailable'}.")
            error = prompt.get('error') or stage.get('generation_error') or evaluation.get('error')
            if error: lines.append('Execution issue: ' + cell(error))
            review = stage.get('final_review') or {}
            if review:
                lines.append('Independent review: ' + normalized(review)['completion_basis'])
                lines.extend('- ' + cell(issue) for issue in review.get('remaining_issues', []))
            else: lines.append('Independent completion review is pending.')
            if evaluation.get('snapshot_path'): lines.append('Preserved evaluated output: `' + evaluation['snapshot_path'] + '`.')
            if stage.get('review', {}).get('prompt'):
                lines.append('The exact improvement prompt is included in the downloadable stage records and the dashboard’s expandable review.')
    lines += ['### Source records and preservation', '[Download the reviewed stage records and definitions](http://127.0.0.1:8765/api/improvement-report-data). Initial records: `results/master_results.json`. Each stage has its own `campaign.json`, reviewer files and preservation audit under `results/improvement_campaign/` (improvement 2 in `pass_2/`).',
              'The continuing model output lives in `results/further-work/<model>/<task>/<initial run>/artifacts/`. Earlier output versions and scores stay under `evaluations/<evaluation id>/`. Prompt text, token logs and changes are preserved in `revision.json` and the per-stage `completion_pass*_prompt.txt` files.']
    for stage in data['rounds']:
        audit = stage['audit']
        if audit: lines.append(f"Improvement {stage['round']} preservation audit: {audit.get('preserved_files_checked', audit.get('initial_files_checked', 0))} files checked; unchanged: {audit.get('preserved_files_unchanged', audit.get('initial_files_unchanged'))}; one prompt per eligible result: {audit.get('one_prompt_per_incomplete_result')}.")
        else: lines.append(f"Improvement {stage['round']} final preservation audit will run when the stage finishes.")
    return '\n'.join(line if line.startswith(('|', '- ')) else '\n' + line + '\n' for line in lines)
