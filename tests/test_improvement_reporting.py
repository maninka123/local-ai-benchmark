from markdown_it import MarkdownIt
from extensions import improvement_reporting as report

def test_report_preserves_scores_pending_review_and_explains_runtime_failure(tmp_path,monkeypatch):
    monkeypatch.setattr(report,'ROOT',tmp_path)
    entry={'run_id':'one','model':'Model','task':'racing_game','case':None,'status':'needs_final_review','evaluation':{'scores':{'verified_points':8,'pending_points':85},'snapshot_path':'saved/output'},'generation_error':'Model load memory failure'}
    first={**entry,'status':'incomplete_after_first_pass','final_review':{'completed':False,'completion_basis':'Only a menu is saved.'}}
    data={'rounds':[{'round':1,'entries':[first],'evaluated':1,'reviewed':1,'completed':0,'status':'complete','audit':{}},{'round':2,'entries':[entry],'evaluated':1,'reviewed':0,'completed':0,'status':'awaiting_final_reviews','audit':{}}]}
    monkeypatch.setattr(report,'read_json',lambda path,default:[{'run_id':'one','scores':{'verified_points':20,'pending_points':0},'original_scores':{'verified_points':5,'pending_points':85},'task_seconds':60}] if path.name=='master_results.json' else default)
    text=report.section(data);html=MarkdownIt().enable('table').render(text)
    assert '5.0 verified / 85.0 pending' in html and '20.0 verified' not in html
    assert html.count('<table>')==2 and 'Review pending' in html
    assert 'Model load memory failure' in html and 'Only a menu is saved.' in html
    assert '0 fully completed' in html and '60-minute limit' in html
