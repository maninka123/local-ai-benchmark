import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'scripts'))
import run_completion_pass as controller

def test_submission_recovers_saved_request_without_sending_a_second_prompt(tmp_path,monkeypatch):
    folder=tmp_path/'work/artifacts';folder.mkdir(parents=True)
    workspace={'further_folder':str(folder),'revision':None};sent=[]
    def request(client,method,path,payload=None):
        if method=='POST':
            sent.append(payload)
            workspace['revision']={'revision_id':'rev-aabbccddeeff','status':'queued','prompts':[{'update_id':'update-example','name':payload['name'],'prompt':payload['prompt'],'created':'2026-10-12T01:00:00+00:00'}]}
        return workspace
    monkeypatch.setattr(controller,'request',request)
    campaign={'campaign_id':'test','created':'2026-10-12T00:00:00+00:00'}
    entry={'run_id':'initial','model':'example','task':'racing_game','case':None,'review':{'prompt':'The menu is saved. The playable race is missing.'}}
    assert controller.submit(None,campaign,entry)
    recovered={**entry,'status':'ready'}
    assert controller.submit(None,campaign,recovered)
    assert len(sent)==1 and recovered['update_id']==entry['update_id']
    assert (folder.parent/'completion_pass_prompt.txt').read_text()=='The menu is saved. The playable race is missing.'

def test_finished_generation_is_evaluated_but_not_claimed_complete(monkeypatch):
    revision={'revision_id':'rev-aabbccddeeff','current_update_id':'update-example','status':'finished','generation_seconds':12,'evaluations':[]}
    requests=[]
    def request(client,method,path,payload=None):
        requests.append((method,path))
        if method=='POST':revision['status']='queued_score';return revision
        return {'revision':revision}
    monkeypatch.setattr(controller,'request',request)
    entry={'run_id':'initial','model':'example','task':'data_analysis','case':None,'update_id':'update-example','status':'running'}
    controller.monitor(None,entry);controller.monitor(None,entry)
    assert entry['status']=='evaluating' and sum(method=='POST' for method,path in requests)==1
    revision['evaluations']=[{'evaluation_id':'evaluation','update_id':'update-example','scores':{'verified_points':20,'pending_points':80,'complete':True}}]
    controller.monitor(None,entry)
    assert entry['status']=='needs_final_review'

def test_later_user_prompt_is_preserved_instead_of_re_evaluated(monkeypatch):
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':{'current_update_id':'new-user-request'}})
    entry={'run_id':'initial','update_id':'this-pass','status':'running'}
    controller.monitor(None,entry)
    assert entry['status']=='superseded'

def test_completion_review_must_match_this_update(monkeypatch):
    monkeypatch.setattr(controller,'read_json',lambda path,default: [{'run_id':'initial','update_id':'different-update','completed':True}] if path.name=='data_after_reviews.json' else [])
    campaign={'entries':[{'run_id':'initial','update_id':'this-update','status':'needs_final_review'}]}
    controller.collect_final_reviews(campaign)
    assert campaign['entries'][0]['status']=='needs_final_review'

def test_objective_failure_does_not_finish_before_the_assigned_expert_review(monkeypatch):
    campaign={'entries':[{'run_id':'initial','update_id':'current','status':'incomplete_after_first_pass'}]}
    reviews=[]
    monkeypatch.setattr(controller,'read_json',lambda path,default:reviews if path.name=='data_after_reviews.json' else [])
    assert controller.waiting_for_expert_reviews(campaign)
    reviews.append({'run_id':'initial','update_id':'older','completed':False})
    assert controller.waiting_for_expert_reviews(campaign)
    reviews.append({'run_id':'initial','update_id':'current','completed':False})
    assert not controller.waiting_for_expert_reviews(campaign)

def test_initial_completion_does_not_require_an_unnecessary_followup_review(monkeypatch):
    monkeypatch.setattr(controller,'read_json',lambda path,default:[])
    assert not controller.waiting_for_expert_reviews({'entries':[{'run_id':'initial','status':'completed_initial'}]})


def test_recovered_request_needs_review_of_the_fresh_snapshot(monkeypatch):
    entry={'run_id':'initial','update_id':'current','status':'needs_final_review','requires_fresh_review_snapshot':True,'evaluation':{'snapshot_path':'results/evaluations/new'}}
    reviews=[{'run_id':'initial','update_id':'current','completed':False,'evidence_files':['results/evaluations/old/artifacts/report.md']}]
    monkeypatch.setattr(controller,'read_json',lambda path,default:reviews if path.name=='data_after_reviews.json' else [])
    assert controller.waiting_for_expert_reviews({'entries':[entry]})
    controller.collect_final_reviews({'entries':[entry]})
    assert entry['status']=='needs_final_review'
    reviews[0]['evidence_files']=['results\\evaluations\\new\\artifacts\\report.md']
    assert not controller.waiting_for_expert_reviews({'entries':[entry]})


def test_recovered_review_accepts_equivalent_evidence_field():
    entry={'update_id':'current','requires_fresh_review_snapshot':True,'evaluation':{'snapshot_path':'results/evaluations/new'}}
    assert controller.review_matches(entry,{'update_id':'current','basis':'Actual files inspected','evidence':['results/evaluations/new/evaluation.json']})
    assert not controller.review_matches(entry,{'update_id':'current','evidence':['results/evaluations/old/evaluation.json']})


def test_infrastructure_resume_keeps_the_same_prompt_and_preserves_failure(tmp_path,monkeypatch):
    folder=tmp_path/'artifacts';folder.mkdir()
    prompt={'update_id':'current','prompt':'Finish the saved work.','error':'Sandbox startup: Docker unavailable','performance':{'inference_calls':0}}
    revision={'current_update_id':'current','status':'failed','prompts':[prompt]}
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':revision})
    monkeypatch.setattr(controller,'sandbox_ready',lambda:True)
    saved=[];monkeypatch.setattr(controller,'write_json',lambda path,info:saved.append(info))
    entry={'run_id':'initial','update_id':'current','status':'infrastructure_recovery','further_folder':str(folder),'model':'test','task':'detective'}
    assert controller.recover_infrastructure(None,{'entries':[entry]})
    assert entry['status']=='running' and len(saved[0]['prompts'])==1
    assert saved[0]['current_update_id']=='current'
    assert saved[0]['infrastructure_recovery_history'][0]['failed_prompt_attempt']['error']=='Sandbox startup: Docker unavailable'


def test_infrastructure_resume_refuses_a_model_attempt_that_started(tmp_path,monkeypatch):
    import pytest
    revision={'current_update_id':'current','status':'failed','prompts':[{'error':'Sandbox startup: Docker unavailable','performance':{'inference_calls':1}}]}
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':revision})
    monkeypatch.setattr(controller,'sandbox_ready',lambda:True)
    entry={'run_id':'initial','update_id':'current','status':'infrastructure_recovery','further_folder':str(tmp_path),'model':'test','task':'detective'}
    with pytest.raises(ValueError,match='already began'):
        controller.recover_infrastructure(None,{'entries':[entry]})


def test_connection_refused_recovery_requires_no_inference_or_tool_work():
    prompt={'error':'[WinError 10061] Connection refused','performance':dict.fromkeys(['inference_calls','input_tokens','output_tokens','tool_calls','tool_failures'],0)}
    assert controller.pre_inference_failure(prompt)
    for key in prompt['performance']:
        changed={**prompt,'performance':{**prompt['performance'],key:1}}
        assert not controller.pre_inference_failure(changed)
    assert not controller.pre_inference_failure({'error':'Unrelated failure','performance':prompt['performance']})
    assert not controller.pre_inference_failure({'error':prompt['error'],'performance':{'inference_calls':0}})


def test_dead_server_blocks_new_requests_without_launching_on_other_platforms(monkeypatch):
    monkeypatch.setattr(controller,'model_server_ready',lambda:False)
    monkeypatch.setattr(controller,'model_server_pause',lambda:None)
    monkeypatch.setattr(controller.os,'name','posix')
    campaign={}
    assert not controller.runtime_ready(campaign)
    assert 'no prompt submitted' in campaign['last_infrastructure_wait']['reason']


def test_authorised_maintenance_pause_is_respected_without_restart(monkeypatch):
    monkeypatch.setattr(controller,'model_server_ready',lambda:False)
    monkeypatch.setattr(controller,'model_server_pause',lambda:'Local AI is temporarily paused for the authorised video render.')
    monkeypatch.setattr(controller.subprocess,'run',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Must not restart a paused server')))
    campaign={}
    assert not controller.runtime_ready(campaign)
    assert 'video render' in campaign['last_infrastructure_wait']['reason']
    assert 'server_restart_history' not in campaign


def test_connection_refused_scored_attempt_is_preserved_for_same_request_recovery(monkeypatch):
    evaluation={'evaluation_id':'failed-startup','update_id':'current','scores':{'verified_points':0}}
    revision={'current_update_id':'current','status':'failed','error':'[WinError 10061]', 'evaluations':[evaluation], 'prompts':[{'update_id':'current','error':'[WinError 10061]','performance':dict.fromkeys(['inference_calls','input_tokens','output_tokens','tool_calls','tool_failures'],0)}]}
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':revision})
    entry={'run_id':'initial','update_id':'current','model':'example','task':'detective','final_review':{'completed':False}}
    controller.monitor(None,entry)
    assert entry['status']=='infrastructure_recovery'
    assert entry['ignored_evaluation_ids']==['failed-startup']
    assert entry['infrastructure_attempts'][0]['evaluation']==evaluation
    assert entry['historical_final_reviews']==[{'completed':False}]


def test_external_transport_interruption_resumes_with_original_budget_checkpoint(tmp_path,monkeypatch):
    prompt={'update_id':'current','prompt':'Same request','seconds':120,'performance':{'inference_calls':1},'error':'ReadError'}
    checkpoint={'update_id':'current','used_seconds':120,'started_calls':1,'reason':'Authorised external maintenance interrupted transport'}
    revision={'current_update_id':'current','status':'failed','prompts':[prompt],'resume_checkpoint':checkpoint}
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':revision})
    monkeypatch.setattr(controller,'sandbox_ready',lambda:True)
    monkeypatch.setattr(controller,'model_server_ready',lambda:True)
    saved=[];monkeypatch.setattr(controller,'write_json',lambda path,info:saved.append(info))
    entry={'run_id':'initial','update_id':'current','status':'infrastructure_resume','further_folder':str(tmp_path/'artifacts'),'model':'test','task':'detective'}
    assert controller.recover_infrastructure(None,{'entries':[entry]})
    assert saved[0]['resume_checkpoint']==checkpoint
    assert len(saved[0]['prompts'])==1 and entry['status']=='running'


def test_infrastructure_continuation_rejects_a_reset_budget(tmp_path,monkeypatch):
    import pytest
    revision={'current_update_id':'current','status':'failed','prompts':[{'seconds':120,'performance':{'inference_calls':1}}],'resume_checkpoint':{'update_id':'current','used_seconds':0,'started_calls':0,'reason':'Authorised external maintenance interrupted transport'}}
    monkeypatch.setattr(controller,'request',lambda *args:{'revision':revision})
    monkeypatch.setattr(controller,'sandbox_ready',lambda:True)
    entry={'run_id':'initial','update_id':'current','status':'infrastructure_resume'}
    with pytest.raises(ValueError,match='already began'):
        controller.recover_infrastructure(None,{'entries':[entry]})
