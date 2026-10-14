import importlib.util,json,sys,types
from pathlib import Path

def test_one_hour_queue_retains_results_and_retries_timeouts_last(tmp_path,monkeypatch):
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec=importlib.util.spec_from_file_location('extended_campaign',scripts/'run_extended_pilot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    models=[{'name':'vision','digest':'v','vision':True},{'name':'text','digest':'t','vision':False}]
    (tmp_path/'results').mkdir();(tmp_path/'logs').mkdir()
    def prior(task,case,run_id,error=None):return {'run_id':run_id,'model':models[0],'task':task,'case':case,'pilot':True,'repetition':1,'protocol_hash':'old','error':error,'performance':{}}
    original=[prior('data_analysis',None,'old-timeout','Task inference deadline exceeded'),prior('detective','case_01','old-success')]
    (tmp_path/'results/master_results.json').write_text(json.dumps(original))
    (tmp_path/'results/setup_validation.json').write_text('{"all_passed":true}')
    monkeypatch.setattr(module,'ROOT',tmp_path);monkeypatch.setattr(module,'discover',lambda:models)
    monkeypatch.setattr(module,'config',lambda:{'benchmark':{'task_timeout_seconds':3600}})
    monkeypatch.setattr(module,'source_hash',lambda:'new');monkeypatch.setattr(module,'export',lambda:None)
    monkeypatch.setitem(sys.modules,'generate_report',types.SimpleNamespace(main=lambda:None))
    monkeypatch.setattr(sys,'argv',['run_extended_pilot.py','--baseline','old'])
    calls=[]
    def attempt(model,task,case,rep,pilot):
        calls.append((model['name'],task,case));run_id=f'new-{len(calls)}'
        return {'run_id':run_id,'run_path':f'outputs/{run_id}','model':model,'task':task,'case':case,'error':'Task inference deadline exceeded' if len(calls) in (1,6) else None,'performance':{}}
    monkeypatch.setattr(module,'run_attempt',attempt)
    module.main()
    campaign=json.loads((tmp_path/'results/active_campaign.json').read_text())
    assert campaign['status']=='complete'
    assert len(campaign['entries'])==9 and all(e['status']=='done' for e in campaign['entries'])
    assert campaign['run_ids'][:2]==['old-timeout','old-success']
    assert calls[-2:]==[('vision','data_analysis',None),('vision','racing_game',None)]
    assert len(calls)==7 and not (tmp_path/'logs/gpu-controller.lock').exists()
    module.main()  # resume performs no duplicate work
    assert len(calls)==7
    assert not module.timed_out({'error':'Browser tool command timeout','performance':{}})
