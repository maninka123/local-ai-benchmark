import pytest
from dashboard.backend import judging as module

def record(number, completed, quality):
    return {'number':number,'completed':completed,'raw_score':quality,'criteria':[{'name':'Quality','points':quality,'max_points':100}]}

def rows(monkeypatch,attempts):
    monkeypatch.setattr(module,'read_json',lambda path,default: [{'run_id':'test','model':'test','task':'detective','attempts':attempts}] if path.name=='detective.json' else [])
    return module.reviewed_rows()[0]

@pytest.mark.parametrize('attempt,score',[(1,100),(2,60),(3,30)])
def test_completed_bands(monkeypatch,attempt,score):
    result=rows(monkeypatch,[record(n,n==attempt,80) for n in range(1,attempt+1)])
    assert result['attempts'][-1]['score']==score

def test_incomplete_does_not_get_early_completion_bonus(monkeypatch):
    result=rows(monkeypatch,[record(1,False,80),record(2,False,50),record(3,False,0)])
    assert [a['score'] for a in result['attempts']]==[None,None,0]
    assert result['first_completed_attempt'] is None

def test_bad_rubric_rejected(monkeypatch):
    with pytest.raises(ValueError):rows(monkeypatch,[record(1,False,101)])

def test_case_average_not_sum(monkeypatch):
    monkeypatch.setattr(module,'reviewed_rows',lambda:[{'model':'m','task':'detective','sensory_track':'text_only_detective','final':{'score':10,'raw_score':50,'completed':False}},{'model':'m','task':'detective','sensory_track':'text_only_detective','final':{'score':20,'raw_score':80,'completed':False}}])
    result=module.judging()['aggregates'][0]
    assert result['score']==15 and result['cases']==2 and result['completed']==0
