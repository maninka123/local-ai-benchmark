import json,sys
from pathlib import Path
import pytest
from fastapi import HTTPException
from benchmark.util import write_json,read_json
from dashboard.backend import modifications as revisions
from dashboard.backend import parameters

@pytest.fixture
def revision_lab(tmp_path,monkeypatch):
    original=tmp_path/'models'/'original';(original/'input').mkdir(parents=True);(original/'artifacts').mkdir()
    (original/'input'/'public.csv').write_text('x\n1\n')
    (original/'artifacts'/'report.md').write_text('Original report')
    (original/'artifacts'/'node_modules').mkdir();(original/'artifacts'/'node_modules'/'skip.js').write_text('dependency')
    scores={'verified_points':8,'pending_points':85,'quality_score':None,'categories':{'report':None}}
    write_json(original/'scores.json',scores)
    row={'run_id':'baseline','run_path':'models/original','model':{'name':'test','digest':'digest'},'task':'data_analysis','case':None,'task_seconds':123,'performance':{'output_tokens':42},'scores':scores}
    write_json(tmp_path/'results'/'master_results.json',[row])
    monkeypatch.setattr(revisions,'ROOT',tmp_path);monkeypatch.setattr(revisions,'BASE',tmp_path/'results'/'modifications');monkeypatch.setattr(revisions,'start_queue',lambda:None)
    return tmp_path,original,row

def test_revision_and_parent_are_independent_of_original(revision_lab):
    root,original,row=revision_lab
    before=(original/'scores.json').read_bytes();master=(root/'results'/'master_results.json').read_bytes()
    info=revisions.create({'run_id':'baseline','name':'Better report','prompt':'Improve the report'})
    path=revisions.location(info['revision_id']);assert (path/'input'/'public.csv').read_bytes()==(original/'input'/'public.csv').read_bytes()
    assert not (path/'artifacts'/'node_modules').exists()
    (path/'artifacts'/'report.md').write_text('Updated report');info['status']='finished';info['generation_status']='finished';write_json(path/'revision.json',info)
    child=revisions.create({'run_id':'baseline','name':'Second version','prompt':'Add details','parent_revision_id':info['revision_id']})
    childpath=revisions.location(child['revision_id']);assert (childpath/'artifacts'/'report.md').read_text()=='Updated report'
    (childpath/'artifacts'/'report.md').write_text('Child report')
    assert (path/'artifacts'/'report.md').read_text()=='Updated report'
    assert (original/'artifacts'/'report.md').read_text()=='Original report'
    assert (original/'scores.json').read_bytes()==before and (root/'results'/'master_results.json').read_bytes()==master
    assert info['original_seconds']==123 and info['original_scores']==row['scores']
    with pytest.raises(HTTPException):revisions.safe_artifact(path,'../../models/original/scores.json')
    with pytest.raises(HTTPException):revisions.create({'run_id':'baseline','name':4,'prompt':'text'})
    with pytest.raises(HTTPException):revisions.location('../baseline')


def test_user_pause_blocks_execution_but_keeps_saved_results_available(revision_lab):
    root,original,row=revision_lab
    flag=root/'results/improvement_campaign/stop_requested';flag.parent.mkdir(parents=True);flag.write_text('User pause')
    before=(original/'scores.json').read_bytes()
    assert revisions.workspace('baseline')['processing_paused']
    for action in [lambda:revisions.continue_work('baseline',{'prompt':'Finish it'}),lambda:revisions.create({'run_id':'baseline','name':'Update','prompt':'Finish it'}),lambda:revisions.evaluate('rev-aabbccddeeff')]:
        with pytest.raises(HTTPException) as error:action()
        assert error.value.status_code==423
    assert (original/'scores.json').read_bytes()==before
    assert not list((root/'results/further-work').glob('*/*/*/revision.json'))


def test_recent_activity_retains_cursor_and_complete_downloadable_log(revision_lab):
    root,original,row=revision_lab
    info=revisions.create({'run_id':'baseline','name':'Update','prompt':'Finish it'})
    path=revisions.location(info['revision_id']);stream=path/'live_events.jsonl'
    stream.write_text('\n'.join(json.dumps({'kind':'output','text':str(i),'timestamp':str(i)}) for i in range(1200)),encoding='utf-8')
    result=revisions.detail(info['revision_id'],tail=5)
    assert result['next_cursor']==1200
    assert [e['text'] for e in result['events']]==['1195','1196','1197','1198','1199']
    assert len(stream.read_text().splitlines())==1200
    assert not revisions.detail(info['revision_id'],after=1200,tail=5)['events']

def test_reevaluation_snapshots_and_scores_append(revision_lab,monkeypatch):
    root,original,row=revision_lab
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    import revision_worker as worker
    monkeypatch.setattr(worker,'ROOT',root)
    class Box:
        def __init__(self,path):self.path=path
        def __enter__(self):return self
        def __exit__(self,*args):pass
    class Scorer:
        @staticmethod
        def score(path,box):
            (path/'artifacts'/'report.md').write_text('Scorer reproduction modifies snapshot only')
            return {'verified_points':20,'pending_points':80,'quality_score':None}
    monkeypatch.setattr(worker,'Sandbox',Box);monkeypatch.setattr(worker,'SCORERS',{'data_analysis':Scorer})
    info=revisions.create({'run_id':'baseline','name':'Scoring check','prompt':'Improve report'});path=revisions.location(info['revision_id']);info['generation_status']='finished'
    info=worker.score(path,info);first=dict(info['evaluations'][0]);info=worker.score(path,info)
    assert len(info['evaluations'])==2 and info['evaluations'][0]==first
    assert info['evaluations'][0]['snapshot_path']!=info['evaluations'][1]['snapshot_path']
    assert (path/'artifacts'/'report.md').read_text()=='Original report'
    assert info['original_scores']==row['scores']
    assert read_json(original/'scores.json')==row['scores']

def test_parameter_estimate_includes_fused_experts_and_shared_weights(monkeypatch):
    parameters.calculated.cache_clear()
    monkeypatch.setattr(Path,'is_file',lambda _:True)
    monkeypatch.setattr(parameters,'tensor_directory',lambda _: [('blk.0.ffn_gate_up_exps.weight',[2,6,8]),('blk.0.ffn_down_exps.weight',[3,2,8]),('shared.weight',[2,3]),('attention.weight',[2,2])])
    result=parameters.calculated('fixture','FROM fixture.gguf','moe',8,2,154)
    assert result['total']==154 and result['active']==46
    assert result['percent']==pytest.approx(100*46/154)
    assert 'not observed' in result['basis']
    parameters.calculated.cache_clear()


def test_embedded_vision_weights_are_separate_from_text_active_estimate(monkeypatch):
    parameters.calculated.cache_clear()
    monkeypatch.setattr(Path,'is_file',lambda _:True)
    monkeypatch.setattr(parameters,'tensor_directory',lambda _: [('blk.0.ffn_up_exps.weight',[4,8]),('attention.weight',[2,2]),('v.encoder.weight',[3,4])])
    result=parameters.calculated('vision-fixture','FROM fixture.gguf','moe',8,2,48)
    assert result['total']==36 and result['active']==12 and result['auxiliary_parameters']==12
    parameters.calculated.cache_clear()


def test_manual_ratings_append_audit_and_preserve_automatic_score(revision_lab,monkeypatch):
    import sqlite3
    from dashboard.backend import app as dashboard
    from benchmark.scoring import aggregate_scorer
    from benchmark.scoring.writing_scorer import RUBRICS
    root,original,row=revision_lab
    monkeypatch.setattr(dashboard,'ROOT',root);monkeypatch.setattr(aggregate_scorer,'export',lambda:None)
    rubric=root/'evaluation_private'/'scoring_config'/'human_rubric.md';rubric.parent.mkdir(parents=True);rubric.write_text('Fixed review rubric')
    with sqlite3.connect(root/'results'/'benchmark.sqlite') as db:
        db.execute('CREATE TABLE reviews (run_id TEXT,timestamp TEXT,reviewer TEXT,original_json TEXT,corrected_json TEXT,reason TEXT)')
    before=(original/'scores.json').read_bytes();categories={k:maximum/2 for k,maximum in RUBRICS['data_analysis'].items()}
    payload={'reviewer':'Fixture reviewer','reason':'Fixture observations of report and charts','categories':categories,'complete':False}
    first=dashboard.review('baseline',payload);second=dashboard.review('baseline',{**payload,'reason':'Second independent fixture review'})
    assert first['quality_score']==50 and first['original_scores']==row['scores']
    assert first['reason']!=second['reason'] and (original/'scores.json').read_bytes()==before
    audits=[json.loads(line) for line in (original/'manual_reviews.jsonl').read_text().splitlines()]
    assert len(audits)==2 and audits[0]==first
    with sqlite3.connect(root/'results'/'benchmark.sqlite') as db:assert db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]==2
    with pytest.raises(HTTPException):dashboard.review('baseline',{**payload,'categories':{**categories,'visualization':999}})

def test_further_prompts_share_one_folder_and_preserve_initial(revision_lab):
    root,original,row=revision_lab
    before={p:p.read_bytes() for p in [original/'artifacts'/'report.md',original/'scores.json',root/'results'/'master_results.json']}
    assert revisions.workspace('baseline')['revision'] is None
    first=revisions.continue_work('baseline',{'prompt':'Improve the report'})['revision']
    path=revisions.location(first['revision_id'])
    assert path==revisions.working_path(row) and not (path/'artifacts'/'node_modules').exists()
    (path/'artifacts'/'report.md').write_text('First update')
    first.update(status='finished',generation_status='finished',generation_seconds=17,performance={'input_tokens':12,'output_tokens':24})
    first['prompts'][-1].update(status='finished',seconds=17)
    first['evaluations']=[{'evaluation_id':'old-score','seconds':2,'scores':{'verified_points':10},'update_id':first['current_update_id']}]
    write_json(path/'revision.json',first)
    second=revisions.continue_work('baseline',{'prompt':'Keep that and add more details','name':'More details'})['revision']
    assert second['revision_id']==first['revision_id'] and revisions.location(second['revision_id'])==path
    assert (path/'artifacts'/'report.md').read_text()=='First update'
    assert len(second['prompts'])==2 and second['prompts'][0]['prompt']=='Improve the report'
    assert second['evaluations']==first['evaluations'] and second['current_update_id']!=first['evaluations'][0]['update_id']
    assert second['original_scores']==row['scores'] and second['original_seconds']==123
    totals=revisions.workspace('baseline');assert totals['extra_seconds']==19 and totals['extra_output_tokens']==24
    with pytest.raises(HTTPException) as error:revisions.continue_work('baseline',{'prompt':'Do not queue over active work'})
    assert error.value.status_code==409
    assert all(p.read_bytes()==data for p,data in before.items())
    assert len(revisions.records())==1

def test_legacy_work_is_adopted_without_double_counting(revision_lab):
    _,original,row=revision_lab
    legacy=revisions.create({'run_id':'baseline','name':'First saved update','prompt':'Make a change'})
    source=revisions.location(legacy['revision_id']);(source/'artifacts'/'report.md').write_text('Legacy update')
    legacy.update(status='finished',generation_status='finished',generation_seconds=15,performance={'output_tokens':30,'input_tokens':10})
    write_json(source/'revision.json',legacy)
    path,info=revisions.prepare_work(row)
    assert path!=source and info['revision_id']==legacy['revision_id']
    assert (path/'artifacts'/'report.md').read_text()=='Legacy update'
    assert (source/'artifacts'/'report.md').read_text()=='Legacy update'
    assert len(revisions.records())==1 and revisions.workspace('baseline')['extra_seconds']==15
    assert revisions.location(legacy['revision_id'])==path
    assert (original/'artifacts'/'report.md').read_text()=='Original report'

def test_folder_button_opens_only_selected_result_and_blocks_cross_site(revision_lab,monkeypatch):
    from types import SimpleNamespace
    root,original,row=revision_lab;opened=[]
    monkeypatch.setattr(revisions.os,'startfile',lambda path:opened.append(Path(path)),raising=False)
    request=SimpleNamespace(headers={'origin':'http://127.0.0.1:8765'},base_url='http://127.0.0.1:8765/')
    revisions.open_folder('baseline',{'kind':'initial'},request)
    revisions.open_folder('baseline',{'kind':'further'},request)
    assert opened==[(original/'artifacts').resolve(),(revisions.working_path(row)/'artifacts').resolve()]
    for p in opened:assert p.is_relative_to(root)
    with pytest.raises(HTTPException):revisions.open_folder('baseline',{'kind':'../../'},request)
    with pytest.raises(HTTPException):revisions.open_folder('baseline',{'kind':'initial'},SimpleNamespace(headers={'origin':'https://example.com'},base_url=request.base_url))
    assert len(opened)==2

def test_written_detective_further_work_retains_variant_and_rubric(revision_lab,monkeypatch):
    from extensions import text_detective
    root,original,row=revision_lab
    row.update(task='detective',case='case_03',sensory_track=text_detective.TRACK)
    write_json(root/'results/master_results.json',[row])
    path,info=revisions.prepare_work(row)
    assert info['sensory_track']==text_detective.TRACK
    assert read_json(path/'identity.json')['sensory_track']==text_detective.TRACK
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    import revision_worker as worker
    monkeypatch.setattr(worker,'ROOT',root)
    class Box:
        def __init__(self,path):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
    monkeypatch.setattr(worker,'Sandbox',Box)
    monkeypatch.setattr(worker,'SCORERS',{})  # Using the native visual rubric would fail.
    monkeypatch.setattr(text_detective,'score',lambda *args:{'rubric':text_detective.RUBRIC,'verified_points':40,'pending_points':60})
    result=worker.score(path,info)
    assert result['evaluations'][0]['error'] is None
    assert result['evaluations'][0]['scores']['rubric']==text_detective.RUBRIC
    assert result['original_scores']==row['scores']

def test_written_detective_manual_review_uses_its_own_bounds(revision_lab,monkeypatch):
    import sqlite3
    from extensions import text_detective
    from dashboard.backend import app as dashboard
    from benchmark.scoring import aggregate_scorer
    root,original,row=revision_lab
    row.update(task='detective',case='case_03',sensory_track=text_detective.TRACK)
    row['scores']={'rubric':text_detective.RUBRIC,'categories':{k:None for k in text_detective.RUBRIC}}
    write_json(root/'results/master_results.json',[row])
    rubric=root/'evaluation_private/scoring_config/human_rubric.md';rubric.parent.mkdir(parents=True)
    rubric.write_text('General instructions\n## Data\nData\n## Detective\nVisual guide')
    monkeypatch.setattr(dashboard,'ROOT',root);monkeypatch.setattr(aggregate_scorer,'export',lambda:None)
    with sqlite3.connect(root/'results/benchmark.sqlite') as db:
        db.execute('CREATE TABLE reviews (run_id TEXT,timestamp TEXT,reviewer TEXT,original_json TEXT,corrected_json TEXT,reason TEXT)')
    guide=dashboard.review_guide('baseline')
    assert 'images not supplied' in guide['guide'] and 'visual_evidence' not in guide['rubric']
    payload={'reviewer':'Fixture reviewer','reason':'Checked D01-D03','categories':text_detective.RUBRIC,'complete':True}
    result=dashboard.review('baseline',payload)
    assert result['quality_score']==100 and result['original_scores']==row['scores']
    assert result['rubric_sha256']==text_detective.protocol()
    with pytest.raises(HTTPException):dashboard.review('baseline',{**payload,'categories':{**text_detective.RUBRIC,'visual_evidence':20}})
