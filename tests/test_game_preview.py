from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from dashboard.backend import app as api


def test_missing_page_and_outside_build_do_not_start_a_viewer(tmp_path,monkeypatch):
    monkeypatch.setattr(api,'ROOT',tmp_path)
    with pytest.raises(HTTPException) as error:api.launch_site('example',tmp_path/'missing')
    assert error.value.status_code==409
    with pytest.raises(HTTPException) as error:api.launch_site('example',tmp_path.parent)
    assert error.value.status_code==409


def test_viewer_waits_for_ready_uses_docker_assigned_port_and_reuses_it(tmp_path,monkeypatch):
    monkeypatch.setattr(api,'ROOT',tmp_path)
    dist=tmp_path/'dist';dist.mkdir();(dist/'index.html').write_text('Trusted fixture')
    commands=[]
    def run(args,**kwargs):
        commands.append(args)
        return SimpleNamespace(returncode=0,stdout='127.0.0.1:43210\n' if args[1]=='port' else 'container',stderr='')
    monkeypatch.setattr(api.subprocess,'run',run)
    monkeypatch.setattr(api,'viewer_ready',lambda url:True)
    monkeypatch.setattr(api,'viewers',{})
    first=api.launch_site('fixture',dist)
    assert first['url']=='http://127.0.0.1:43210'
    assert api.launch_site('fixture',dist)==first and len(commands)==2
    assert '127.0.0.1::8000' in commands[0] and '--read-only' in commands[0]
    api.stop_game('fixture');api.stop_game('fixture')
    assert not api.viewers and len(commands)==3


def test_start_failure_cleans_partial_container(tmp_path,monkeypatch):
    monkeypatch.setattr(api,'ROOT',tmp_path);monkeypatch.setattr(api,'viewers',{})
    dist=tmp_path/'dist';dist.mkdir();(dist/'index.html').write_text('Fixture')
    commands=[]
    def run(args,**kwargs):
        commands.append(args);return SimpleNamespace(returncode=1,stdout='',stderr='Docker unavailable')
    monkeypatch.setattr(api.subprocess,'run',run)
    with pytest.raises(HTTPException) as error:api.launch_site('fixture',dist)
    assert error.value.status_code==503 and commands[-1][1:3]==['rm','-f']
    assert not api.viewers


def test_revision_preview_rejects_unscored_current_work_but_opens_saved_snapshot(tmp_path,monkeypatch):
    from dashboard.backend import modifications
    folder=tmp_path/'revision';snapshot=folder/'evaluations'/'eval-old'
    (snapshot/'artifacts/game/dist').mkdir(parents=True)
    info={'task':'racing_game','workspace_mode':True,'current_update_id':'new','evaluations':[{'evaluation_id':'eval-old','update_id':'old','snapshot_path':str(snapshot),'scores':{'evidence':{'build_success':True}}}]}
    monkeypatch.setattr(api,'ROOT',tmp_path);monkeypatch.setattr(api,'read_json',lambda path:info)
    monkeypatch.setattr(modifications,'location',lambda _:folder)
    monkeypatch.setattr(api,'launch_site',lambda name,dist:{'view_id':name})
    with pytest.raises(HTTPException) as error:api.launch_revision_game('rev-example')
    assert error.value.status_code==409
    assert api.launch_revision_game('rev-example','eval-old')['view_id']=='rev-example-eval-old'
    with pytest.raises(HTTPException) as error:api.launch_revision_game('rev-example','missing')
    assert error.value.status_code==404
    info['evaluations'][0]['snapshot_path']=str(tmp_path/'outside')
    with pytest.raises(HTTPException) as error:api.launch_revision_game('rev-example','eval-old')
    assert error.value.status_code==409


def test_closing_revision_removes_all_its_preview_containers(monkeypatch,tmp_path):
    from dashboard.backend import modifications
    monkeypatch.setattr(modifications,'location',lambda _:tmp_path)
    monkeypatch.setattr(api,'viewers',{'rev-a-eval-1':{'container':'one'},'rev-a-eval-2':{'container':'two'},'rev-b-eval-1':{'container':'other'}})
    removed=[];monkeypatch.setattr(api.subprocess,'run',lambda args,**kwargs:removed.append(args[-1]))
    api.stop_revision_game('rev-a')
    assert removed==['one','two'] and list(api.viewers)==['rev-b-eval-1']

def test_closing_one_snapshot_keeps_other_saved_previews(monkeypatch,tmp_path):
    from dashboard.backend import modifications
    monkeypatch.setattr(modifications,'location',lambda _:tmp_path)
    monkeypatch.setattr(api,'viewers',{'rev-a-eval-1':{'container':'one'},'rev-a-eval-2':{'container':'two'}})
    removed=[];monkeypatch.setattr(api.subprocess,'run',lambda args,**kwargs:removed.append(args[-1]))
    api.stop_revision_game('rev-a','eval-1')
    assert removed==['one'] and list(api.viewers)==['rev-a-eval-2']


def test_compiled_partial_output_can_be_viewed_without_changing_its_score():
    scores={'evidence':{'build_success':False,'browser':{'build':True,'checks':{'canvas':False}}}}
    import copy
    original=copy.deepcopy(scores)
    assert api.has_game_build(scores)
    assert scores==original
    assert not api.has_game_build({'evidence':{'browser':{'build':False}}})
    assert not api.has_game_build(None)


def test_revision_preview_allows_compiled_placeholder_snapshot(tmp_path,monkeypatch):
    from dashboard.backend import modifications
    folder=tmp_path/'revision';snapshot=folder/'evaluations'/'eval-partial'
    (snapshot/'artifacts/game/dist').mkdir(parents=True)
    info={'task':'racing_game','workspace_mode':True,'current_update_id':'current','evaluations':[{'evaluation_id':'eval-partial','update_id':'current','snapshot_path':str(snapshot),'scores':{'evidence':{'build_success':False,'browser':{'build':True}}}}]}
    monkeypatch.setattr(api,'ROOT',tmp_path);monkeypatch.setattr(api,'read_json',lambda path:info)
    monkeypatch.setattr(modifications,'location',lambda _:folder)
    monkeypatch.setattr(api,'launch_site',lambda name,dist:{'view_id':name})
    assert api.launch_revision_game('rev-partial')['view_id']=='rev-partial-eval-partial'


def test_closing_stale_preview_cannot_remove_a_new_session(monkeypatch):
    first='1'*32;second='2'*32
    monkeypatch.setattr(api,'viewers',{api.viewer_key('example',first):{'container':'old'},api.viewer_key('example',second):{'container':'new'}})
    removed=[];monkeypatch.setattr(api.subprocess,'run',lambda args,**kwargs:removed.append(args[-1]))
    api.stop_game('example',first)
    assert removed==['old'] and api.viewer_key('example',second) in api.viewers


def test_preview_session_id_rejects_invalid_values():
    with pytest.raises(HTTPException) as error:api.viewer_key('example','../../other')
    assert error.value.status_code==422
