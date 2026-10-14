"""One reviewed improvement prompt per incomplete saved result; preserve initials."""
import _bootstrap
import hashlib,json,time,os,subprocess,copy
from contextlib import contextmanager
from pathlib import Path
import httpx
from benchmark.util import ROOT,read_json,write_json,now,artifact_files
from extensions.windows_io import atomic_replacements
from extensions.completion_reviews import normalized

BASE=ROOT/'results'/'improvement_campaign'
STATE=BASE/'campaign.json'
API='http://127.0.0.1:8765/api'
TERMINAL={'finished','failed','interrupted'}
PASS_NUMBER=1
METADATA_PREFIX='completion_pass'

def prompt_title(entry):
    return f'Completion pass {PASS_NUMBER} - '+entry['task'].replace('_',' ')+((' '+entry['case']) if entry.get('case') else '')

@contextmanager
def keep_running():
    """Keep an unattended Windows run awake; restore the request on exit."""
    if os.name!='nt':
        yield
        return
    import ctypes
    api=ctypes.windll.kernel32.SetThreadExecutionState
    if not api(0x80000001):raise OSError('Unable to request system wakefulness for the unattended run')
    try:yield
    finally:api(0x80000000)

def fingerprints():
    files=[]
    for row in read_json(ROOT/'results/master_results.json',[]):
        run=ROOT/row['run_path']
        files.extend([run/'result.json',run/'scores.json'])
        files.extend(artifact_files(run/'artifacts'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}

def request(client,method,path,payload=None):
    response=client.request(method,API+path,json=payload)
    response.raise_for_status()
    return response.json()

def save(campaign):
    campaign['updated']=now();write_json(STATE,campaign)

def collect_reviews(campaign):
    reviews={r['run_id']:r for name in ['data','racing','detective'] for r in read_json(BASE/(name+'_reviews.json'),[])}
    for entry in campaign['entries']:
        review=reviews.get(entry['run_id'])
        if not review or entry['status'] not in ['awaiting_review','ready']:continue
        entry['review']=review
        if review.get('current_completed'):
            entry['status']='completed_initial' if review.get('initial_completed') else 'completed_before_pass'
            entry['completion_basis']=review.get('completion_basis')
        else:
            if not review.get('prompt','').strip():raise ValueError('Incomplete result has no reviewed prompt: '+entry['run_id'])
            entry['status']='ready';entry['prompt_sha256']=hashlib.sha256(review['prompt'].encode()).hexdigest()
    return reviews

def collect_final_reviews(campaign):
    reviews={r['run_id']:normalized(r) for name in ['objective','data','racing','detective'] for r in read_json(BASE/(name+'_after_reviews.json'),[])}
    for entry in campaign['entries']:
        review=reviews.get(entry['run_id'])
        if not review or entry['status'] not in ['needs_final_review','incomplete_after_first_pass'] or not review_matches(entry,review) or entry.get('final_review')==review:continue
        entry['final_review']=review
        entry['status']='completed_first_pass' if review.get('completed') else 'incomplete_after_first_pass'
        if entry.get('further_folder'):
            write_json(Path(entry['further_folder']).parent/(METADATA_PREFIX+'_after_review.json'),review)

def triage_pending(campaign):
    pending=[e for e in campaign['entries'] if e['status']=='needs_final_review' and not e.get('objective_triaged')]
    if not pending:return
    from triage_completion_outputs import main as triage
    triage()
    for entry in pending:entry['objective_triaged']=True

def review_matches(entry,review):
    if review.get('update_id')!=entry.get('update_id'):return False
    if not entry.get('requires_fresh_review_snapshot'):return True
    snapshot=(entry.get('evaluation') or {}).get('snapshot_path','').replace('\\','/').rstrip('/')
    return bool(snapshot) and any(str(p).replace('\\','/').startswith(snapshot+'/') for p in normalized(review)['evidence_files'])

def waiting_for_expert_reviews(campaign):
    reviews=[r for name in ['data','racing','detective'] for r in read_json(BASE/(name+'_after_reviews.json'),[]) if isinstance(r.get('completed'),bool)]
    return any(not any(r['run_id']==e['run_id'] and review_matches(e,r) for r in reviews) for e in campaign['entries'] if e.get('update_id'))

def sandbox_ready():
    try:
        result=subprocess.run(['docker','info','--format','{{.ServerVersion}}'],capture_output=True,text=True,timeout=20)
        return result.returncode==0 and bool(result.stdout.strip())
    except (OSError,subprocess.TimeoutExpired):return False

def pre_inference_failure(prompt):
    """Only startup failures with proof that no model/tool work occurred."""
    metrics=prompt.get('performance',{})
    if metrics.get('inference_calls')!=0:return False
    error=prompt.get('error') or ''
    if 'Sandbox startup:' in error:return True
    return ('WinError 10061' in error or 'Connection refused' in error) and all(metrics.get(k)==0 for k in ['input_tokens','output_tokens','tool_calls','tool_failures'])

def model_server_ready():
    from benchmark.util import config
    try:
        with httpx.Client(timeout=3) as client:
            response=client.get(config()['benchmark']['base_url']+'/api/version')
            response.raise_for_status()
            return bool(response.json().get('version'))
    except (httpx.HTTPError,ValueError):return False

def model_server_pause():
    """Respect an explicit maintenance responder owned by another local task."""
    from benchmark.util import config
    try:
        with httpx.Client(timeout=3) as client:
            response=client.get(config()['benchmark']['base_url']+'/api/version')
            if response.status_code==503:
                message=response.json().get('error','')
                if 'temporarily paused' in message.lower():return message
    except (httpx.HTTPError,ValueError):pass
    return None

def runtime_ready(campaign):
    """Wait for dependencies; restart the existing local server with its settings."""
    if not model_server_ready():
        pause=model_server_pause()
        if pause:
            campaign['last_infrastructure_wait']={'timestamp':now(),'reason':pause,'resume':'Wait for the other authorised task to release its maintenance responder; no requests or restarts during this hold.'}
            return False
        campaign['last_infrastructure_wait']={'timestamp':now(),'reason':'Local model server unavailable; no prompt submitted.'}
        # Rate limit failed launches. Use the established startup script, which
        # verifies readiness and reuses an already running server.
        last=campaign.get('last_server_restart_epoch',0)
        startup=ROOT.parent/'start_ollama.ps1'
        if os.name=='nt' and startup.is_file() and time.time()-last>=60:
            campaign['last_server_restart_epoch']=time.time()
            try:
                result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(startup)],capture_output=True,text=True,timeout=45)
                campaign.setdefault('server_restart_history',[]).append({'timestamp':now(),'returncode':result.returncode,'stdout':result.stdout[-2000:],'stderr':result.stderr[-2000:]})
            except (OSError,subprocess.TimeoutExpired) as error:
                campaign.setdefault('server_restart_history',[]).append({'timestamp':now(),'error':str(error)})
        if not model_server_ready():return False
    if not sandbox_ready():
        campaign['last_infrastructure_wait']={'timestamp':now(),'reason':'Docker sandbox unavailable; no prompt submitted.'}
        return False
    return True

def recover_infrastructure(client,campaign):
    entry=next((e for e in campaign['entries'] if e['status'] in ['infrastructure_recovery','infrastructure_resume','evaluation_recovery']),None)
    if not entry:return False
    if not sandbox_ready():return True
    workspace=request(client,'GET','/workspaces/'+entry['run_id']);info=workspace['revision']
    if info.get('current_update_id')!=entry['update_id']:
        entry.update(status='superseded',error='A later user request replaced the recovery request.');return True
    if info['status'] not in TERMINAL:return True
    if entry['status'] in ['infrastructure_recovery','infrastructure_resume']:
        prompt=info['prompts'][-1]
        checkpoint=info.get('resume_checkpoint') if entry['status']=='infrastructure_resume' else None
        resume_valid=bool(checkpoint and checkpoint.get('update_id')==entry['update_id'] and checkpoint.get('reason')=='Authorised external maintenance interrupted transport' and checkpoint.get('used_seconds')==prompt.get('seconds') and checkpoint.get('started_calls')==prompt.get('performance',{}).get('inference_calls'))
        if not resume_valid and not pre_inference_failure(prompt):
            raise ValueError('Refusing to repeat a model attempt that already began: '+entry['run_id'])
        if entry['status']=='infrastructure_resume' and not resume_valid:
            raise ValueError('Infrastructure continuation has no matching saved budget checkpoint: '+entry['run_id'])
        if 'Sandbox startup:' not in (prompt.get('error') or '') and not model_server_ready():return True
        info.setdefault('infrastructure_recovery_history',[]).append({'timestamp':now(),'update_id':entry['update_id'],'failed_prompt_attempt':copy.deepcopy(prompt),'reason':'Continue the same interrupted request with its remaining original budget.' if resume_valid else 'Infrastructure failed before any model call; resume the same saved request.'})
        prompt.update(status='queued',error=None)
        info.update(status='queued',generation_status='queued',error=None,operation='update')
        write_json(Path(entry['further_folder']).parent/'revision.json',info)
        entry['status']='running'
        print('RESUME SAME SAVED REQUEST',entry['model'],entry['task'],entry['update_id'],flush=True)
    else:
        request(client,'POST','/modifications/'+entry['revision_id']+'/evaluate')
        entry['status']='evaluating'
        print('RETRY EVALUATION ONLY',entry['model'],entry['task'],flush=True)
    return True

def monitor(client,entry):
    workspace=request(client,'GET','/workspaces/'+entry['run_id'])
    revision=workspace.get('revision')
    if not revision:return
    # Only follow this pass's request. Never overwrite a newer user request.
    if revision.get('current_update_id')!=entry['update_id']:
        entry.update(status='superseded',error='A later user request replaced the monitored request. Saved history is preserved.');return
    entry['revision_status']=revision['status'];entry['seconds']=revision.get('generation_seconds',0)
    evaluation=next((e for e in reversed(revision.get('evaluations',[])) if e.get('update_id')==entry['update_id'] and e['evaluation_id'] not in entry.get('ignored_evaluation_ids',[])),None)
    if evaluation:
        entry.update(status='needs_final_review' if evaluation.get('scores') else 'evaluation_failed',evaluation_id=evaluation['evaluation_id'],evaluation=evaluation,
                     generation_error=revision.get('error'),finished=now())
        prompt=next((p for p in reversed(revision.get('prompts',[])) if p.get('update_id')==entry['update_id']),{})
        if pre_inference_failure(prompt):
            entry.setdefault('ignored_evaluation_ids',[]).append(evaluation['evaluation_id'])
            entry.setdefault('infrastructure_attempts',[]).append({'timestamp':now(),'evaluation':copy.deepcopy(evaluation),'error':prompt['error']})
            if entry.get('final_review'):
                entry.setdefault('historical_final_reviews',[]).append(entry.pop('final_review'))
            entry.pop('evaluation',None)
            entry.pop('evaluation_id',None)
            entry['status']='infrastructure_recovery'
        print('EVALUATED',entry['model'],entry['task'],entry.get('case') or '',
              'verified=',(evaluation.get('scores') or {}).get('verified_points'),'pending=',(evaluation.get('scores') or {}).get('pending_points'),flush=True)
    elif revision['status'] in TERMINAL:
        # Re-evaluate even a partial or failed response. No second model prompt.
        request(client,'POST','/modifications/'+revision['revision_id']+'/evaluate')
        entry['status']='evaluating';print('SCORE',entry['model'],entry['task'],entry.get('case') or '',flush=True)
    else:entry['status']='evaluating' if revision['status'] in ['queued_score','reevaluating'] else 'running'

def submit(client,campaign,entry):
    title=prompt_title(entry)
    prompt=entry['review']['prompt'];workspace=request(client,'GET','/workspaces/'+entry['run_id']);prior=workspace.get('revision')
    previous=next((p for p in (prior or {}).get('prompts',[]) if p['name']==title and p['prompt']==prompt and p['created']>=campaign['created']),None)
    if previous:
        revision=prior;update=previous
    else:
        if prior and prior['status'] not in TERMINAL:return False
        workspace=request(client,'POST','/workspaces/'+entry['run_id']+'/prompt',{'name':title,'prompt':prompt})
        revision=workspace['revision'];update=revision['prompts'][-1]
    entry.update(status='running',revision_id=revision['revision_id'],update_id=update['update_id'],submitted=update['created'],
                 prior_saved_requests=len(revision['prompts'])-1,further_folder=workspace['further_folder'])
    # Put the review and exact prompt beside the continuing workspace, outside
    # candidate artifacts. The model receives only the submitted outcome prompt.
    folder=Path(workspace['further_folder']).parent
    write_json(folder/(METADATA_PREFIX+'_review.json'),{'campaign_id':campaign['campaign_id'],'run_id':entry['run_id'],'update_id':update['update_id'],'review':entry['review']})
    (folder/(METADATA_PREFIX+'_prompt.txt')).write_text(prompt,encoding='utf-8')
    print('PROMPT',entry['model'],entry['task'],entry.get('case') or '',update['update_id'],flush=True)
    return True

def main():
    BASE.mkdir(exist_ok=True);campaign=read_json(STATE)
    from run_missing_detective_initials import initialize
    initialize()
    if not campaign:
        initial=read_json(BASE/'baseline_inventory.json',[])
        campaign={'campaign_id':'completion-pass-2026-10-12','name':'First completion pass','created':now(),'status':'running','prompt_limit':1,
                  'note':'One outcome-focused prompt per incomplete saved result. Initial outputs and scores are immutable. Written and visual Detective remain separate. Completion requires independent review; pending quality scores remain pending.',
                  'entries':[{'run_id':r['run_id'],'model':r['model']['name'],'task':r['task'],'case':r.get('case'),'sensory_track':r['sensory_track'],'status':'awaiting_review'} for r in initial]}
        write_json(BASE/'initial_fingerprints.json',fingerprints());save(campaign)
    with httpx.Client(timeout=90) as client:
        while True:
            if (BASE/'stop_requested').exists():
                campaign['status']='stopped';save(campaign);print('STOP requested: no further prompts submitted.',flush=True);return
            collect_reviews(campaign)
            triage_pending(campaign)
            collect_final_reviews(campaign)
            active=next((e for e in campaign['entries'] if e['status'] in ['running','evaluating']),None)
            try:
                if active:monitor(client,active)
                else:
                    if recover_infrastructure(client,campaign):
                        save(campaign);time.sleep(5);continue
                    from run_missing_detective_initials import run_next
                    if run_next(campaign):
                        save(campaign)
                        continue
                    new_ids={e.get('run_id') for e in read_json(BASE/'missing_initials.json',{}).get('entries',[]) if e['status']=='done'}
                    ready=next((e for e in campaign['entries'] if e['status']=='ready' and e['run_id'] in new_ids),None)
                    if not ready:ready=next((e for e in campaign['entries'] if e['status']=='ready'),None)
                    if ready:
                        if not sandbox_ready():
                            campaign['last_infrastructure_wait']={'timestamp':now(),'reason':'Docker sandbox unavailable; no prompt submitted.'}
                            save(campaign);time.sleep(5);continue
                        submit(client,campaign,ready)
            except (httpx.HTTPError,OSError) as error:
                campaign['last_controller_error']={'timestamp':now(),'error':str(error)};print('Controller wait:',error,flush=True)
            save(campaign)
            missing_initials=any(e['status']!='done' for e in read_json(BASE/'missing_initials.json',{}).get('entries',[]))
            pending=missing_initials or waiting_for_expert_reviews(campaign) or any(e['status'] in ['awaiting_review','ready','running','evaluating','needs_final_review','infrastructure_recovery','evaluation_recovery'] for e in campaign['entries'])
            campaign['status']='awaiting_final_reviews' if pending and not any(e['status'] in ['awaiting_review','ready','running','evaluating'] for e in campaign['entries']) else 'running'
            if not pending:
                original=read_json(BASE/'initial_fingerprints.json',{})
                changed=[p for p,sha in original.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha]
                counts={}
                for entry in campaign['entries']:
                    if not entry.get('further_folder'):continue
                    info=read_json(Path(entry['further_folder']).parent/'revision.json',{})
                    counts[entry['run_id']]=sum(p['created']>=campaign['created'] and p['name'].startswith('Completion pass 1 - ') for p in info.get('prompts',[]))
                write_json(BASE/'execution_validation.json',{'timestamp':now(),'initial_files_checked':len(original),'initial_files_unchanged':not changed,'changed_paths':changed,
                           'one_prompt_per_incomplete_result':all(n==1 for n in counts.values()),'prompt_counts':counts,'entries':len(campaign['entries'])})
                if changed or not all(n==1 for n in counts.values()):
                    campaign.update(status='validation_failed',error='Initial preservation or one-prompt audit failed. See execution_validation.json.');save(campaign)
                    raise RuntimeError(campaign['error'])
                campaign.update(status='complete',finished=now());save(campaign)
                print('ALL ONE-PROMPT UPDATES, EVALUATIONS AND INDEPENDENT COMPLETION REVIEWS FINISHED.',flush=True);return
            time.sleep(5)

if __name__=='__main__':
    with keep_running(),atomic_replacements(ROOT):main()
