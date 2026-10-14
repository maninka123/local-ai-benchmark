import sys,hashlib
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'scripts'))
import run_missing_detective_initials as initials
from benchmark.util import write_json,read_json

def test_new_initial_appended_once_and_existing_fingerprints_preserved(tmp_path,monkeypatch):
    base=tmp_path/'results/improvement_campaign';base.mkdir(parents=True)
    run=tmp_path/'models/example/run';(run/'artifacts').mkdir(parents=True)
    for name in ['result.json','scores.json','artifacts/report.md']:(run/name).write_text(name)
    row={'run_id':'new-initial','run_path':'models/example/run','model':{'name':'example'},'task':'detective','case':'case_03'}
    monkeypatch.setattr(initials,'ROOT',tmp_path);monkeypatch.setattr(initials,'BASE',base)
    write_json(base/'initial_fingerprints.json',{'old/initial':'original-sha'})
    campaign={'entries':[]}
    initials.append_result(row,campaign);initials.append_result(row,campaign)
    assert len(campaign['entries'])==len(read_json(base/'baseline_inventory.json'))==1
    assert campaign['entries'][0]['status']=='awaiting_review'
    hashes=read_json(base/'initial_fingerprints.json')
    assert hashes['old/initial']=='original-sha'
    assert hashes[str(Path('models/example/run/artifacts/report.md'))]==hashlib.sha256(b'artifacts/report.md').hexdigest()

def test_finished_initial_plan_does_not_run_again(tmp_path,monkeypatch):
    plan=tmp_path/'missing_initials.json';write_json(plan,{'entries':[{'model':'example','status':'done'}]})
    monkeypatch.setattr(initials,'PLAN',plan)
    monkeypatch.setattr(initials,'attempt',lambda *args:(_ for _ in ()).throw(AssertionError('Must not rerun baseline')))
    assert initials.run_next({'entries':[]}) is False

def test_saved_initial_recovers_after_controller_save_gap_without_rewriting(tmp_path,monkeypatch):
    import json
    base=tmp_path/'results/improvement_campaign';base.mkdir(parents=True)
    run=tmp_path/'models/example/run';(run/'artifacts').mkdir(parents=True)
    row={'run_id':'saved','run_path':'models/example/run','campaign':initials.CAMPAIGN,'model':{'name':'example'},'task':'detective','case':'case_03'}
    original=json.dumps(row).encode();(run/'result.json').write_bytes(original)
    write_json(tmp_path/'results/master_results.json',[row])
    plan=base/'missing_initials.json';write_json(plan,{'entries':[{'model':'example','status':'done','run_id':'saved'}]})
    monkeypatch.setattr(initials,'ROOT',tmp_path);monkeypatch.setattr(initials,'BASE',base);monkeypatch.setattr(initials,'PLAN',plan)
    monkeypatch.setattr(initials,'export',lambda:None)
    monkeypatch.setattr(initials,'config',lambda:{'benchmark':{'task_timeout_seconds':3600}})
    monkeypatch.setattr(initials,'attempt',lambda *args:(_ for _ in ()).throw(AssertionError('Must not repeat model inference')))
    campaign={'entries':[]}
    assert initials.run_next(campaign) is True
    assert campaign['entries'][0]['run_id']=='saved'
    assert (run/'result.json').read_bytes()==original
