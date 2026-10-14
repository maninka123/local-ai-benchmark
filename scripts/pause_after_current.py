"""Finish only the saved current request, evaluate it, then pause processing."""
import _bootstrap
import time,json
import httpx
import run_completion_pass as runner
from benchmark.util import ROOT,read_json,write_json,now
from extensions.windows_io import atomic_replacements

BASE=ROOT/'results/improvement_campaign/pass_2'

def main():
    plan=read_json(BASE/'pause_after_current.json')
    runner.BASE=BASE;runner.STATE=BASE/'campaign.json';runner.PASS_NUMBER=2;runner.METADATA_PREFIX='completion_pass_2'
    ids={entry['update_id'] for entry in plan.get('active',[])}
    with httpx.Client(timeout=90) as client:
        while True:
            campaign=read_json(runner.STATE)
            entries=[e for e in campaign['entries'] if e.get('update_id') in ids]
            for entry in entries:
                if entry['status'] in ['running','evaluating']:
                    runner.monitor(client,entry)
            runner.collect_final_reviews(campaign)
            campaign['status']='pausing';runner.save(campaign)
            pending=[e for e in entries if e['status'] in ['running','evaluating']]
            if not pending:break
            print(json.dumps({'pausing_after_current':True,'current':[(e['model'],e['task'],e['status']) for e in pending]}),flush=True)
            time.sleep(10)
        # The model job and score job have finished. Freeze the queue before
        # unloading so a dashboard request cannot start another operation.
        (BASE.parent/'stop_requested').write_text('User paused after the current prompt at '+now(),encoding='utf-8')
        for model in {e['model'] for e in entries}:
            response=client.post('http://127.0.0.1:11434/api/generate',json={'model':model,'keep_alive':0})
            response.raise_for_status()
        deadline=time.monotonic()+300
        while runner.waiting_for_expert_reviews({'entries':entries}) and time.monotonic()<deadline:
            time.sleep(5)
            campaign=read_json(runner.STATE)
            runner.collect_final_reviews(campaign);runner.save(campaign)
            entries=[e for e in campaign['entries'] if e.get('update_id') in ids]
        campaign.update(status='paused',paused_at=now(),pause_reason='User requested finish current prompt, then stop and wait for explicit resume.')
        runner.save(campaign)
        plan.update(finished=now(),status='paused',active_results=[{k:e.get(k) for k in ['run_id','model','task','update_id','status','evaluation_id']} for e in entries])
        write_json(BASE/'pause_after_current.json',plan)
        from generate_report import main as report
        report()
        print('PAUSED. Current result saved; model unloaded. No new prompts will start until explicitly resumed.',flush=True)

if __name__=='__main__':
    with runner.keep_running(),atomic_replacements(ROOT):main()
