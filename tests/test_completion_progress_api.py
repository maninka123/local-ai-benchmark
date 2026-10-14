from dashboard.backend import completion_pass as progress
import pytest
from fastapi import HTTPException

def test_round_selection_keeps_prior_campaign_separate(monkeypatch):
    def read(path,default):
        if path.name=='current_round.json':return {'round':2}
        if path.name=='campaign.json':return {'name':'second' if path.parent.name=='pass_2' else 'first','entries':[]}
        return default
    monkeypatch.setattr(progress,'read_json',read)
    assert progress.overview()['name']=='second'
    assert progress.overview(1)['name']=='first'
    assert progress.overview(2)['round']==2
    with pytest.raises(HTTPException) as error:progress.overview(99)
    assert error.value.status_code==400

def test_progress_ignores_a_completion_review_for_a_different_update(monkeypatch):
    stored={'run_id':'initial','model':'example','task':'detective','status':'needs_final_review','update_id':'current','evaluation':{'scores':{'complete':True}}}
    campaign={'entries':[stored]}
    def read(path,default):
        if path.name=='campaign.json':return campaign
        if path.name=='detective_after_reviews.json':return [{'run_id':'initial','update_id':'older','completed':True}]
        return default
    monkeypatch.setattr(progress,'read_json',read)
    entry=progress.overview()['entries'][0]
    assert entry['status']=='needs_final_review' and 'final_review' not in entry

def test_finished_initial_review_is_visible_without_mutating_controller_state(monkeypatch):
    campaign={'entries':[{'run_id':'initial','model':'example','task':'detective','status':'awaiting_review'}]}
    review={'run_id':'initial','initial_completed':False,'current_completed':False,'prompt':'Complete the missing investigation report.'}
    def read(path,default):
        if path.name=='campaign.json':return campaign
        if path.name=='detective_reviews.json':return [review]
        return default
    monkeypatch.setattr(progress,'read_json',read)
    entry=progress.overview()['entries'][0]
    assert entry['status']=='ready' and entry['review']==review
    assert campaign['entries'][0]['status']=='awaiting_review'


def test_recovery_does_not_display_the_blocked_snapshot_review_as_final(monkeypatch):
    entry={'run_id':'initial','model':'example','task':'detective','status':'needs_final_review','update_id':'current','requires_fresh_review_snapshot':True,'evaluation':{'snapshot_path':'results/evaluations/recovered'}}
    review={'run_id':'initial','update_id':'current','completed':False,'evidence_files':['results/evaluations/failed/artifacts/report.md']}
    def read(path,default):
        if path.name=='campaign.json':return {'entries':[entry]}
        if path.name=='detective_after_reviews.json':return [review]
        return default
    monkeypatch.setattr(progress,'read_json',read)
    assert progress.overview()['entries'][0]['status']=='needs_final_review'
    review['evidence_files']=['results/evaluations/recovered/artifacts/report.md']
    assert progress.overview()['entries'][0]['status']=='incomplete_after_first_pass'


def test_resumed_progress_includes_time_used_before_pause(tmp_path,monkeypatch):
    entry={'run_id':'initial','model':'example','task':'racing_game','status':'running','update_id':'current','revision_id':'rev-example'}
    def read(path,default):
        if path.name=='campaign.json':return {'entries':[entry]}
        if path.name=='revision.json':return {'status':'running','operation':'update','resume_checkpoint':{'update_id':'current','used_seconds':120}}
        return default
    monkeypatch.setattr(progress,'read_json',read);monkeypatch.setattr(progress,'location',lambda _:tmp_path);monkeypatch.setattr(progress,'elapsed',lambda _:10)
    assert progress.overview()['progress']['current']['elapsed_seconds']==130
