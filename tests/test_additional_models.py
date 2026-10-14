import json,sys
from pathlib import Path
from benchmark.util import read_json,write_json
from extensions import text_detective as written

def test_added_queue_keeps_saved_attempts_and_has_three_distinct_slots(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    from run_additional_models import plan,MODELS
    old={'model':'old','task':'data_analysis','case':None,'repetition':1,'run_id':'immutable','status':'done'}
    campaign={'entries':[old.copy()],'run_ids':['immutable']}
    plan(campaign,MODELS,'text-detective');plan(campaign,MODELS,'text-detective')
    assert campaign['entries'][0]==old and campaign['run_ids']==['immutable']
    assert len(campaign['entries'])==15
    for model in MODELS:
        slots=[e for e in campaign['entries'] if e['model']==model]
        if model.startswith('qwen3-vl:'):
            assert [e['task'] for e in slots]==['data_analysis','racing_game','detective','detective','detective']
            assert [e['case'] for e in slots[2:]]==['case_01','case_02','case_03']
            assert all(e['sensory_track']=='native_multimodal' for e in slots[2:])
        else:
            assert [e['task'] for e in slots]==['data_analysis','racing_game','detective']
            assert slots[-1]['sensory_track']==written.TRACK and slots[-1]['case']=='case_03'

def test_written_workspace_removes_only_its_copied_images(tmp_path):
    source=tmp_path/'dataset';(source/'images').mkdir(parents=True)
    (source/'images/V01.png').write_bytes(b'image remains in dataset')
    run=tmp_path/'run';(run/'input/images').mkdir(parents=True)
    (run/'input/images/V01.png').write_bytes((source/'images/V01.png').read_bytes())
    (run/'input/case_brief.md').write_text('Public brief')
    write_json(run/'identity.json',{'case':'case_03'})
    assert written.workspace(lambda *args:run,{},'detective','case_03')==run
    assert not list((run/'input/images').glob('*.png'))
    assert (source/'images/V01.png').read_bytes()==b'image remains in dataset'
    assert read_json(run/'identity.json')['sensory_track']==written.TRACK
    assert 'unavailable' in written.prompt() and sum(written.RUBRIC.values())==100

def test_written_score_rejects_visual_support_without_claiming_completion(tmp_path,monkeypatch):
    from benchmark.scoring import detective_scorer
    truth=tmp_path/'evaluation_private/ground_truth';truth.mkdir(parents=True)
    write_json(truth/'case_03.json',{'responsible_person':None,'identifiable':False,'timeline':[]})
    monkeypatch.setattr(detective_scorer,'ROOT',tmp_path)
    run=tmp_path/'run';(run/'artifacts').mkdir(parents=True)
    write_json(run/'identity.json',{'case':'case_03'})
    for name in ['timeline.json','evidence_analysis.json']:write_json(run/'artifacts'/name,{'exhibits':['D01','D02']})
    (run/'artifacts/investigation_report.md').write_text('Written evidence leaves the identity uncertain.')
    write_json(run/'artifacts/conclusions.json',{'responsible_person':None,'conclusion':'Insufficient evidence','exhibits':['D01','D02']})
    first=written.score(run)
    assert first['categories']['logic']==25 and first['categories']['uncertainty']==15
    assert 'visual_evidence' not in first['rubric'] and first['pending_points']==60
    assert first['quality_score'] is None and not first['complete']
    write_json(run/'artifacts/conclusions.json',{'responsible_person':None,'conclusion':'Insufficient evidence','exhibits':['D01','V01']})
    second=written.score(run)
    assert second['categories']['logic']==0 and second['evidence']['unsupported_conclusion_references']==['V01']

def test_added_controller_resumes_and_retries_deadline_last(tmp_path,monkeypatch):
    import types
    from benchmark.harness import metrics_collector
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    import run_additional_models as controller
    models=[{'name':name,'digest':str(i)} for i,name in enumerate(controller.MODELS)]
    (tmp_path/'logs').mkdir();(tmp_path/'models').mkdir()
    old={'run_id':'old','run_path':'models/old','model':{'name':'old','digest':'old'},'task':'data_analysis','case':None,'repetition':1,'sensory_track':'text_and_tools'}
    write_json(tmp_path/'models/old/result.json',old)
    original=(tmp_path/'models/old/result.json').read_bytes()
    write_json(tmp_path/'results/master_results.json',[old])
    write_json(tmp_path/'results/setup_validation.json',{'all_passed':True})
    write_json(tmp_path/'results/active_campaign.json',{'entries':[{'model':'old','task':'data_analysis','case':None,'status':'done'}],'run_ids':['old']})
    monkeypatch.setattr(controller,'ROOT',tmp_path);monkeypatch.setattr(controller,'discover',lambda:models)
    monkeypatch.setattr(controller,'source_hash',lambda:'cohort')
    monkeypatch.setattr(controller,'config',lambda:{'benchmark':{'task_timeout_seconds':3600}})
    monkeypatch.setitem(sys.modules,'generate_report',types.SimpleNamespace(main=lambda:None))
    monkeypatch.setattr(metrics_collector,'collect',lambda run:{'generation_tps':12.3})
    def export():write_json(tmp_path/'results/master_results.json',[read_json(p) for p in (tmp_path/'models').glob('*/result.json')])
    monkeypatch.setattr(controller,'export',export)
    calls=[]
    def attempt(model,entry):
        calls.append((model['name'],entry['task'],entry.get('retry',False)))
        name='new-'+str(len(calls));run=tmp_path/'models'/name
        row={**entry,'run_id':name,'run_path':'models/'+name,'model':model,'pilot':True,'protocol_hash':'cohort',
             'campaign':'additional_three_models','error':'Task inference deadline exceeded' if len(calls)==1 else None,
             'config':{'benchmark':{'task_timeout_seconds':3600}},'performance':{'generation_tps':12.3}}
        write_json(run/'result.json',row)
        for file in ['scores.json','performance.json']:write_json(run/file,{})
        (run/'hardware_metrics.csv').write_text('timestamp\n')
        return row
    monkeypatch.setattr(controller,'attempt',attempt)
    controller.main([])
    campaign=read_json(tmp_path/'results/active_campaign.json')
    assert campaign['status']=='complete' and len(campaign['entries'])==16
    assert calls[-1]==(models[0]['name'],'data_analysis',True) and len(calls)==15
    assert all(e['status']=='done' for e in campaign['entries'])
    assert (tmp_path/'models/old/result.json').read_bytes()==original
    assert not (tmp_path/'logs/gpu-controller.lock').exists()
    controller.main([])
    assert len(calls)==15
    validation=read_json(tmp_path/'results/additional_models_validation.json')
    assert validation['original_results_unchanged'] and validation['attempts']==15
    assert all(c['weighted_tps_correct'] and c['files_saved'] and not c['images_supplied'] for c in validation['checks'])

def test_native_dispatch_retains_actions_and_rejects_other_tools():
    import pytest
    from extensions.gpt_oss_transport import translate
    from benchmark.harness.runner import parse_actions
    calls=[{'function':{'name':'sandbox_dispatch','arguments':{'tool':'write','path':'/output/file.py','content':'print("test")\n'}}}]
    assert json.loads(translate(calls))=={'actions':[calls[0]['function']['arguments']]}
    with pytest.raises(ValueError):parse_actions(translate([{'function':{'name':'container.exec','arguments':{'cmd':'whoami'}}}]))
    with pytest.raises(ValueError):parse_actions(translate([{'function':{'name':'sandbox_dispatch','arguments':{'tool':'python'}}}]))
    with pytest.raises(ValueError):parse_actions(translate(calls*5))

def test_named_native_functions_map_to_validated_sandbox_actions():
    from extensions.gpt_oss_transport import TOOLS,ACTION_FIELDS,translate
    from benchmark.harness.runner import parse_actions
    assert {t['function']['name'] for t in TOOLS}=={'bench_'+name for name in ACTION_FIELDS}
    calls=[{'function':{'name':'bench_python','arguments':{'code':'print(42)'}}},
           {'function':{'name':'bench_finish','arguments':'{"summary":"Actual saved outputs"}'}}]
    assert parse_actions(translate(calls))==[{'tool':'python','code':'print(42)'},
                                            {'tool':'finish','summary':'Actual saved outputs'}]

def test_infrastructure_recovery_preserves_saved_failed_result(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    import run_additional_models as controller
    monkeypatch.setattr(controller,'ROOT',tmp_path)
    run=tmp_path/'models/failed'
    row={'run_id':'failed','status':'failed','error':'PermissionError(13, Access is denied)',
         'model':{'name':controller.MODELS[1]},'task':'racing_game','case':None}
    write_json(run/'result.json',row);original=(run/'result.json').read_bytes()
    write_json(tmp_path/'logs/current_task.json',{'run_path':'models/failed'})
    campaign={'entries':[{'model':controller.MODELS[1],'task':'racing_game','case':None,'status':'running','additional_models':True}], 'run_ids':[]}
    controller.recover_save_error(campaign);controller.recover_save_error(campaign)
    assert campaign['entries'][0]['run_id']=='failed' and campaign['entries'][0]['status']=='done'
    assert len(campaign['entries'])==2 and campaign['entries'][1]['retry_kind']=='infrastructure_recovery'
    assert campaign['entries'][1]['retry_of']=='failed' and campaign['entries'][1]['status']=='pending'
    assert campaign['run_ids']==['failed'] and (run/'result.json').read_bytes()==original

def test_compatibility_recovery_keeps_failure_and_queues_once(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'scripts'))
    from run_additional_models import recover
    entry={'model':'gpt-oss:20b','task':'data_analysis','status':'done','run_id':'failed','additional_models':True,'retry':False}
    campaign={'entries':[entry.copy()],'run_ids':['failed']}
    history=[{'run_id':'failed','status':'failed','error':'error parsing tool call'}]
    recover(campaign,history);recover(campaign,history)
    assert campaign['entries'][0]==entry and campaign['run_ids']==['failed']
    assert len(campaign['entries'])==2
    assert campaign['entries'][1]['retry_of']=='failed' and campaign['entries'][1]['retry_kind']=='compatibility_recovery'

def test_native_parser_feedback_consumes_one_call_without_inventing_tokens(tmp_path,monkeypatch):
    import asyncio,pytest
    from extensions import gpt_oss_transport as transport
    from benchmark.harness.runner import parse_actions
    class Base:
        def __init__(self,*args):self.calls=0
        async def generate(self):
            self.calls+=1
            raise RuntimeError('error parsing tool call: malformed native JSON')
    monkeypatch.setattr(transport,'OllamaAdapter',Base)
    instance=transport.adapter({'name':'gpt-oss:20b'},tmp_path,100)
    output=asyncio.run(instance.generate())
    assert instance.calls==1 and output.usage is None
    assert output.metadata['token_counters']=='unavailable'
    with pytest.raises(ValueError):parse_actions(output.completion)
    class OtherFailure(Base):
        async def generate(self):raise RuntimeError('Connection lost')
    monkeypatch.setattr(transport,'OllamaAdapter',OtherFailure)
    with pytest.raises(RuntimeError,match='Connection lost'):asyncio.run(transport.adapter({'name':'gpt-oss:20b'},tmp_path,100).generate())

