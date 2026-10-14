"""Read-only progress for the reviewed, one-prompt completion campaign."""
from fastapi import APIRouter,HTTPException
from datetime import datetime,timezone
from benchmark.util import ROOT,read_json,now
from dashboard.backend.modifications import location,elapsed
from extensions.completion_reviews import normalized
router=APIRouter(prefix='/api/completion-pass')
FINISHED={'needs_final_review','completed_first_pass','incomplete_after_first_pass','evaluation_failed','superseded'}

@router.get('')
def overview(round:int=0):
    parent=ROOT/'results/improvement_campaign'
    selected=round or read_json(parent/'current_round.json',{}).get('round',1)
    if selected not in (1,2):raise HTTPException(400,'Choose improvement 1 or 2.')
    base=parent if selected==1 else parent/'pass_2'
    campaign=read_json(base/'campaign.json',{})
    initials=read_json(parent/'missing_initials.json',{}).get('entries',[]) if selected==1 else []
    initial_reviews={r['run_id']:r for name in ['data','racing','detective'] for r in read_json(base/(name+'_reviews.json'),[])}
    reviews={r['run_id']:normalized(r) for name in ['objective','data','racing','detective'] for r in read_json(base/(name+'_after_reviews.json'),[])}
    entries=[];current=None
    for stored in campaign.get('entries',[]):
        entry=dict(stored)
        initial_review=initial_reviews.get(entry['run_id'])
        if entry['status'] in ['awaiting_review','ready'] and initial_review:
            entry['review']=initial_review
            entry['status']=('completed_initial' if initial_review.get('initial_completed') else 'completed_before_pass') if initial_review.get('current_completed') else 'ready'
        review=reviews.get(entry['run_id'])
        snapshot=(entry.get('evaluation') or {}).get('snapshot_path','').replace('\\','/').rstrip('/')
        fresh_review=not entry.get('requires_fresh_review_snapshot') or (bool(snapshot) and review and any(str(p).replace('\\','/').startswith(snapshot+'/') for p in review.get('evidence_files',[])))
        if entry['status']=='needs_final_review' and review and fresh_review and review.get('update_id')==entry.get('update_id'):
            entry.update(final_review=review,status='completed_first_pass' if review.get('completed') else 'incomplete_after_first_pass')
        if entry.get('revision_id'):
            try:
                path=location(entry['revision_id']);revision=read_json(path/'revision.json',{})
                entry['saved_requests']=len(revision.get('prompts',[]))
                entry['package_changes']=revision.get('model_identity_history',[])
                if entry['status'] in ['running','evaluating']:
                    calls=path/'inference_calls.jsonl'
                    entry['live_status']=revision.get('status');entry['elapsed_seconds']=elapsed(revision)
                    checkpoint=revision.get('resume_checkpoint')
                    if checkpoint and checkpoint.get('update_id')==entry.get('update_id') and revision.get('operation')=='update':
                        entry['elapsed_seconds']+=checkpoint.get('used_seconds',0)
                    entry['call_count']=sum(1 for l in calls.read_text(encoding='utf-8').splitlines() if l.strip()) if calls.exists() else 0
                    entry['allowed_seconds']=revision.get('settings',{}).get('task_timeout_seconds',3600)
                    current=entry
            except Exception:pass
        entries.append(entry)
    initial=next((e for e in initials if e['status']=='running'),None)
    if initial and not current:
        live=read_json(ROOT/'logs/current_task.json',{})
        if live.get('model')!=initial['model'] or live.get('task')!='detective':live={}
        started=live.get('inference_start',initial['started'])
        current={**initial,'run_id':'','live_status':'Initial written-evidence test','allowed_seconds':3600,
                 'elapsed_seconds':max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()),'initial_test':True,
                 'call_count':live.get('completed_calls',0)}
    planned=[e for e in entries if e['status'] not in ['completed_initial','completed_before_pass']]
    finished=sum(e['status'] in FINISHED for e in planned)
    rounds=[{'round':number,'name':state.get('name'),'status':state.get('status')} for number,path in [(1,parent),(2,parent/'pass_2')] if (state:=read_json(path/'campaign.json',{}))]
    return {**campaign,'round':selected,'rounds':rounds,'entries':entries,'missing_initials':initials,'generated_at':now(),'progress':{'finished':finished,'total':len(planned),'percent':100*finished/len(planned) if planned else 0,
             'completed_initial':sum(e['status']=='completed_initial' for e in entries),'completed_first_pass':sum(e['status']=='completed_first_pass' for e in entries),'current':current},
            'review_note':'Completion labels come from a separate review of the actual outputs. Automatic completion flags alone are insufficient. Subjective quality scores remain pending until rated. Each saved Detective case is separate.'}
