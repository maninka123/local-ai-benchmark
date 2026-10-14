import json,sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'scripts'))
import triage_completion_outputs as triage

def setup(tmp_path,monkeypatch,missing=False):
    base=tmp_path/'results/improvement_campaign';base.mkdir(parents=True)
    run=tmp_path/'results/evaluation';art=run/'artifacts';art.mkdir(parents=True)
    for name in ['analysis.py','findings.json']:(art/name).write_text('{}')
    if not missing:(art/'report.md').write_text('Report content')
    scores={'complete':True,'evidence':{'figures':['f'+str(i) for i in range(6)],'writing':{'words':2000},'reproducibility':{'executed':True,'exit_code':0}}}
    entry={'run_id':'initial','update_id':'update1','task':'data_analysis','status':'needs_final_review','evaluation':{'snapshot_path':'results/evaluation','scores':scores}}
    (base/'campaign.json').write_text(json.dumps({'entries':[entry]}));(run/'evaluation.json').write_text(json.dumps(entry['evaluation']))
    monkeypatch.setattr(triage,'BASE',base);monkeypatch.setattr(triage,'ROOT',tmp_path)
    return base,run

def test_missing_required_output_cannot_be_overruled_by_completion_flag(tmp_path,monkeypatch):
    base,run=setup(tmp_path,monkeypatch,missing=True);original=(run/'evaluation.json').read_bytes()
    triage.main();reviews=json.loads((base/'objective_after_reviews.json').read_text())
    assert len(reviews)==1 and reviews[0]['completed'] is False
    assert 'report.md' in str(reviews[0]['remaining_issues'])
    assert (run/'evaluation.json').read_bytes()==original

def test_passing_objective_gates_does_not_invent_independent_completion_review(tmp_path,monkeypatch):
    base,run=setup(tmp_path,monkeypatch)
    triage.main()
    assert json.loads((base/'objective_after_reviews.json').read_text())==[]
