"""One additional outcome prompt, preserving the baseline and first improvement."""
import _bootstrap
import hashlib
import time
from pathlib import Path
import httpx
import run_completion_pass as runner
from benchmark.util import ROOT, read_json, write_json, now, source_hash, artifact_files
from extensions.windows_io import atomic_replacements, extended_path

BASE = ROOT / 'results/improvement_campaign/pass_2'
PRIOR = BASE.parent


def digest(path):
    return hashlib.sha256(Path(extended_path(path)).read_bytes()).hexdigest()


def initialize():
    BASE.mkdir(parents=True, exist_ok=True)
    state = read_json(BASE / 'campaign.json')
    if state:
        return state
    previous = read_json(PRIOR / 'campaign.json')
    if previous.get('status') != 'complete':
        raise RuntimeError('First improvement must finish before the third benchmark prompt.')
    frozen = runner.fingerprints()
    for name in ['campaign.json', 'execution_validation.json', 'completion_summary.json']:
        path = PRIOR / name
        if path.is_file():
            frozen[str(path.relative_to(ROOT))] = digest(path)
    entries = []
    for entry in previous['entries']:
        if entry.get('final_review', {}).get('completed'):
            continue
        snapshot = ROOT / entry['evaluation']['snapshot_path']
        for path in artifact_files(Path(extended_path(snapshot))):
            ordinary = Path(str(path).removeprefix('\\\\?\\'))
            frozen[str(ordinary.relative_to(ROOT))] = digest(path)
        parent = Path(entry['further_folder']).parent
        info = read_json(parent / 'revision.json')
        if info.get('current_update_id') != entry['update_id']:
            raise RuntimeError('Latest work changed; review it before submitting: ' + entry['run_id'])
        for name in ['completion_pass_review.json', 'completion_pass_prompt.txt', 'completion_pass_after_review.json']:
            path = parent / name
            if path.is_file():
                frozen[str(path.relative_to(ROOT))] = digest(path)
        entries.append({k: entry.get(k) for k in ['run_id', 'model', 'task', 'case', 'sensory_track']} | {
            'status': 'awaiting_review', 'previous_update_id': entry['update_id'],
            'previous_snapshot_path': entry['evaluation']['snapshot_path'],
            'previous_score': entry['evaluation'].get('scores'),
            'previous_requests': info.get('prompts', []), 'requires_fresh_review_snapshot': True})
    state = {'campaign_id': 'completion-pass-2-' + now()[:10], 'name': 'Improvement 2 (third benchmark prompt)',
             'round': 2, 'created': now(), 'status': 'running', 'prompt_limit': 1,
             'protocol_hash': source_hash(), 'entries': entries,
             'note': 'One new outcome-focused prompt per incomplete result. Baselines, first improvement snapshots, prompts and scores remain preserved. Written and visual Detective are separate. Earlier manual prompts may also exist.'}
    write_json(BASE / 'preserved_fingerprints.json', frozen)
    write_json(BASE / 'campaign.json', state)
    write_json(PRIOR / 'current_round.json', {'round': 2, 'updated': now()})
    return state


def audit(campaign):
    frozen = read_json(BASE / 'preserved_fingerprints.json', {})
    changed = [p for p, sha in frozen.items() if not Path(extended_path(ROOT / p)).is_file() or digest(ROOT / p) != sha]
    counts = {}
    changed_prompts = []
    for entry in campaign['entries']:
        if not entry.get('further_folder'):
            continue
        info = read_json(Path(entry['further_folder']).parent / 'revision.json', {})
        counts[entry['run_id']] = sum(p['created'] >= campaign['created'] and p['name'].startswith('Completion pass 2 - ') for p in info.get('prompts', []))
        # Performance/status fields can evolve on resumption; the saved prior
        # request text, identity and timestamps must never change.
        fields = ['update_id', 'name', 'prompt', 'created']
        saved = {p['update_id']: p for p in info.get('prompts', [])}
        if any(any(saved.get(p['update_id'], {}).get(k) != p.get(k) for k in fields) for p in entry['previous_requests']):
            changed_prompts.append(entry['run_id'])
    valid = not changed and not changed_prompts and len(counts) == len(campaign['entries']) and all(n == 1 for n in counts.values()) and source_hash() == campaign['protocol_hash']
    result = {'timestamp': now(), 'preserved_files_checked': len(frozen), 'preserved_files_unchanged': not changed,
              'changed_paths': changed, 'changed_previous_prompts': changed_prompts,
              'one_prompt_per_incomplete_result': len(counts) == len(campaign['entries']) and all(n == 1 for n in counts.values()),
              'prompt_counts': counts, 'protocol_unchanged': source_hash() == campaign['protocol_hash'], 'valid': valid}
    write_json(BASE / 'execution_validation.json', result)
    return valid


def main():
    campaign = initialize()
    if campaign['status'] == 'complete':
        return
    runner.BASE = BASE
    runner.STATE = BASE / 'campaign.json'
    runner.PASS_NUMBER = 2
    runner.METADATA_PREFIX = 'completion_pass_2'
    with httpx.Client(timeout=90) as client:
        last_report_signature=None
        while True:
            if (PRIOR / 'stop_requested').exists() or (BASE / 'stop_requested').exists():
                campaign.update(status='stopped'); runner.save(campaign); return
            runner.collect_reviews(campaign)
            runner.collect_final_reviews(campaign)
            active = next((e for e in campaign['entries'] if e['status'] in ['running', 'evaluating']), None)
            waiting_infrastructure=False
            try:
                if active:
                    runner.monitor(client, active)
                elif any(e['status'] in ['infrastructure_recovery','infrastructure_resume','evaluation_recovery'] for e in campaign['entries']):
                    if runner.runtime_ready(campaign):
                        runner.recover_infrastructure(client, campaign)
                    else:waiting_infrastructure=True
                else:
                    ready = next((e for e in campaign['entries'] if e['status'] == 'ready'), None)
                    if ready and not runner.runtime_ready(campaign):
                        waiting_infrastructure=True
                    elif ready:
                        review = ready['review']
                        if review.get('previous_update_id') != ready['previous_update_id'] or review.get('previous_snapshot_path') != ready['previous_snapshot_path']:
                            raise ValueError('Prompt review does not match the preceding evaluated output: ' + ready['run_id'])
                        runner.submit(client, campaign, ready)
            except (httpx.HTTPError, OSError) as error:
                campaign['last_controller_error'] = {'timestamp': now(), 'error': str(error)}
                print('Controller wait:', error, flush=True)
            pending = runner.waiting_for_expert_reviews(campaign) or any(e['status'] in ['awaiting_review', 'ready', 'running', 'evaluating', 'needs_final_review', 'infrastructure_recovery', 'infrastructure_resume', 'evaluation_recovery'] for e in campaign['entries'])
            campaign['status'] = 'waiting_infrastructure' if waiting_infrastructure else 'running' if any(e['status'] in ['awaiting_review', 'ready', 'running', 'evaluating'] for e in campaign['entries']) else 'awaiting_final_reviews'
            runner.save(campaign)
            signature=[(e.get('update_id'),e.get('evaluation_id'),e.get('final_review')) for e in campaign['entries']]
            if signature!=last_report_signature:
                from generate_report import main as report
                report()
                last_report_signature=signature
            if not pending:
                if not audit(campaign):
                    campaign.update(status='validation_failed'); runner.save(campaign)
                    raise RuntimeError('Preservation or one-prompt audit failed.')
                campaign.update(status='complete', finished=now()); runner.save(campaign)
                from extensions.improvement_reporting import receipt
                write_json(BASE/'completion_summary.json',receipt())
                report()
                print('SECOND IMPROVEMENT: ALL PROMPTS, EVALUATIONS AND INDEPENDENT REVIEWS FINISHED.', flush=True)
                return
            time.sleep(5)


if __name__ == '__main__':
    with runner.keep_running(), atomic_replacements(ROOT):
        main()
