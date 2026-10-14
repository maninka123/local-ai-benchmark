from fastapi import HTTPException
import pytest
from dashboard.backend import output_history as history

def test_runnable_analysis_does_not_overwrite_failed_completion():
    scores={'evidence':{'reproducibility':{'executed':True,'exit_code':0}}}
    result=history.stage(2,'First improvement','data_analysis',scores,False)
    assert result['outcome']=='failed'
    assert result['readiness']=='Analysis script runs'
    assert history.stage(3,'Second improvement','detective',{},True)['outcome']=='complete'
    assert history.stage(1,'Initial','detective',{},None)['outcome']=='unreviewed'

def test_game_build_and_runtime_errors_are_distinguished():
    assert history.readiness('racing_game',{})=='Build failed'
    scores={'evidence':{'browser':{'build':True,'errors':['Car undefined'],'checks':{'canvas':True}}}}
    assert 'runtime errors' in history.readiness('racing_game',scores)
    scores['evidence']['browser'].update(errors=[],checks={'canvas':False})
    assert 'canvas missing' in history.readiness('racing_game',scores)

@pytest.mark.parametrize('lines',[50,51,None,'25'])
def test_repair_viewer_enforces_strict_source_line_limit(monkeypatch,tmp_path,lines):
    monkeypatch.setattr(history,'repair_location',lambda *args:(tmp_path,{'task':'racing_game','runnable':True,'source_changed_lines':lines}))
    with pytest.raises(HTTPException) as error:history.repair_game('example','repair')
    assert error.value.status_code==409

def test_repair_lookup_blocks_traversal(monkeypatch,tmp_path):
    monkeypatch.setattr(history,'baseline',lambda _: {'run_id':'example'})
    monkeypatch.setattr(history,'working_path',lambda _:tmp_path)
    with pytest.raises(HTTPException) as error:history.repair_location('example','../../elsewhere')
    assert error.value.status_code==404
