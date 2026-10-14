"""Run user-requested revisions in fresh sandboxes without changing benchmark results."""
import _bootstrap,argparse,os,json,time,shutil,hashlib,traceback,base64,asyncio,httpx
from pathlib import Path
from contextlib import asynccontextmanager
from unittest.mock import patch
from inspect_ai import Task,eval
from inspect_ai.dataset import Sample
from inspect_ai.model import Model,GenerateConfig,ChatMessageSystem,ChatMessageUser,ChatMessageAssistant,ContentText,ContentImage
from benchmark.util import ROOT,config,read_json,write_json,append_json,now,artifact_files
from benchmark.harness.runner import local_agent,PROTOCOL,SCORERS
from benchmark.harness.ollama_adapter import OllamaAdapter
from benchmark.harness.execution_manager import Sandbox
from benchmark.harness.resource_monitor import ResourceMonitor
from benchmark.harness.metrics_collector import collect
from extensions import text_detective,gpt_oss_transport,revision_model_identity,windows_io,revision_resume

def inventory(path):return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifact_files(path)}
def event(path,kind,text,**fields):append_json(path/'live_events.jsonl',{'timestamp':now(),'kind':kind,'text':text,**fields})

def live_client(path):
    original=httpx.AsyncClient
    class Response:
        def __init__(self,response):self.response=response
        def __getattr__(self,name):return getattr(self.response,name)
        async def aiter_lines(self):
            buffers={'thinking':'','output':''};last=time.perf_counter()
            def flush():
                for kind,text in buffers.items():
                    if text:event(path,kind,text);buffers[kind]=''
            try:
                async for line in self.response.aiter_lines():
                    try:
                        data=json.loads(line);message=data.get('message',{})
                        buffers['thinking']+=message.get('thinking','');buffers['output']+=message.get('content','')
                        if data.get('done') or time.perf_counter()-last>.15:flush();last=time.perf_counter()
                    except ValueError:pass
                    yield line
            finally:flush()
    class Client(original):
        @asynccontextmanager
        async def stream(self,*args,**kwargs):
            async with super().stream(*args,**kwargs) as response:yield Response(response)
    return Client

def live_adapter(identity,path,deadline):
    adapter=gpt_oss_transport.adapter(identity,path,deadline);generate=adapter.generate
    async def streamed(*args,**kwargs):
        event(path,'status',f'Model call {adapter.calls+1} started.\n')
        # This worker is a separate process. Original token accounting/cancellation is unchanged.
        with patch('benchmark.harness.ollama_adapter.httpx.AsyncClient',live_client(path)):
            return await generate(*args,**kwargs)
    adapter.generate=streamed
    return adapter

def link_dependencies(box,path):
    if (path/'artifacts'/'game').is_dir():box.exec(['bash','-lc','ln -sfn /opt/lab/node_modules /output/game/node_modules'],category='environment_setup')

def update(path,info):
    cfg=config()['benchmark'];before=inventory(path/'artifacts');start=time.perf_counter();error=None
    allowed_seconds,allowed_calls,checkpoint=revision_resume.budget(info,cfg)
    prior_seconds=info.get('generation_seconds',0) if info.get('workspace_mode') else 0
    prior_metrics=revision_resume.prior_hardware(info,checkpoint);before_calls=collect(path)
    measurements=path/'measurements'/info['current_update_id'] if info.get('workspace_mode') else path
    if checkpoint:measurements=measurements/checkpoint['segment_id']
    measurements.mkdir(parents=True,exist_ok=True);monitor=ResourceMonitor(measurements).start()
    event(path,'status','Starting user-prompted revision in its own isolated workspace.\n')
    try:
        if allowed_seconds<=0 or allowed_calls<=0:raise RuntimeError('The saved request has exhausted its original time or call budget; partial work is preserved.')
        with httpx.Client(timeout=60) as client:
            installed=client.get(cfg['base_url']+'/api/tags');installed.raise_for_status()
            current=next((m for m in installed.json()['models'] if m['name']==info['model']['name']),None)
            if not current:raise ValueError('This model is not installed.')
            package=revision_model_identity.check(info['model']['name'],info['model']['digest'],current['digest'])
            if package is None:raise ValueError('The installed package differs from this saved model and is not a verified linked Ollama package.')
            if package['kind']!='same_digest':
                from dashboard.backend.parameters import enrich
                info.setdefault('original_model',dict(info['model']))
                info.setdefault('model_identity_history',[]).append({**package,'timestamp':now(),'update_id':info.get('current_update_id')})
                show=client.post(cfg['base_url']+'/api/show',json={'model':current['name']});show.raise_for_status()
                info['model']=enrich({**info['model'],**current,'show':show.json()})
                identity=read_json(path/'identity.json',{})
                write_json(path/'identity.json',{**identity,'original_digest':info['original_model']['digest'],'digest':current['digest'],'package_check':package})
                write_json(path/'revision.json',info)
                event(path,'status','Ollama '+package['kind'].replace('_',' ')+' recorded separately for further work. Initial model identity and results are preserved.\n')
            client.post(cfg['base_url']+'/api/generate',json={'model':info['model']['name'],'keep_alive':0})
        with Sandbox(path) as box:
            link_dependencies(box,path);deadline=time.perf_counter()+allowed_seconds
            original=text_detective.prompt() if info.get('sensory_track')==text_detective.TRACK else (ROOT/'benchmark'/'prompts'/(info['task']+'_prompt.md')).read_text(encoding='utf-8')
            files='\n'.join(str(p.relative_to(path/'artifacts')) for p in artifact_files(path/'artifacts'))
            previous_prompts='\n'.join(p['name']+': '+p['prompt'] for p in info.get('prompts',[])[:-1])[-12000:]
            text=original+'\n\nEarlier update requests (context only; the latest request overrides conflicting earlier instructions):\n'+previous_prompts+'\n\nLATEST USER REQUEST: '+info['prompt']+'\nExisting output files in /output:\n'+files+'\nApply the latest request to this continuing workspace. Preserve useful work unless the latest request asks to change it. Use the available tool protocol to save real files. Finish with a concise summary of actual changes and limitations. Do not score yourself.'
            content=[ContentText(text=text)]
            if info['task']=='detective':
                content[0].text+='\n'+(path/'input'/'case_brief.md').read_text(encoding='utf-8')
                for doc in sorted((path/'input'/'documents').glob('*')):content[0].text+='\n'+doc.read_text(encoding='utf-8')
                if info.get('sensory_track')!=text_detective.TRACK:
                    for image in sorted((path/'input'/'images').glob('V*.png')):content.extend([ContentText(text='Native visual exhibit '+image.name),ContentImage(image='data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode())])
            system=(ROOT/'benchmark'/'prompts'/'common_system_prompt.md').read_text(encoding='utf-8')+'\n'+PROTOCOL
            messages=[ChatMessageSystem(content=system),ChatMessageUser(content=content)]
            recovered=revision_resume.saved_messages(path,checkpoint)
            if recovered:
                constructors={'system':ChatMessageSystem,'user':ChatMessageUser,'assistant':ChatMessageAssistant}
                messages=[constructors[m['role']](content=m.get('content','')) for m in recovered]
            if checkpoint:event(path,'status',f'Resuming the same saved prompt with {allowed_seconds/60:.1f} minutes and {allowed_calls} calls left. Completed conversation and partial files retained.\n')
            task=Task(name='user_revision',version=1,dataset=[Sample(id=info['revision_id'],input=messages)],
                solver=local_agent(box,info['model'],deadline,path,allowed_calls),metadata={'base_run_id':info['base_run_id'],'revision_id':info['revision_id'],'track':'user-prompted modification','resume_checkpoint':checkpoint},time_limit=int(allowed_seconds)+300)
            model=Model(live_adapter(info['model'],path,deadline),GenerateConfig(max_tokens=cfg['max_output_tokens_per_call'],temperature=0,max_connections=1,max_retries=0))
            logdir=Path('D:/LocalLLM/benchmark-inspect-logs')/info['revision_id'];logdir.mkdir(parents=True,exist_ok=True)
            logs=eval(task,model=model,score=False,log_dir=str(logdir),display='none',max_samples=1,max_tasks=1,fail_on_error=False,log_images=False)
            errors=[s.error.message for s in (logs[0].samples or []) if s.error]
            if logs[0].error:errors.append(logs[0].error.message)
            if errors:raise RuntimeError(errors[0])
    except BaseException as e:error=str(e) or type(e).__name__; (path/'error.txt').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        monitor.stop()
        try:
            with httpx.Client(timeout=30) as client:client.post(cfg['base_url']+'/api/generate',json={'model':info['model']['name'],'keep_alive':0})
        except Exception:pass
    elapsed_seconds=time.perf_counter()-start;performance={**collect(path),**monitor.summary()}
    if info.get('workspace_mode'):
        for key in ['peak_vram_bytes','peak_ram_bytes','peak_inference_rss_bytes','peak_gpu_temperature_c']:
            performance[key]=max((x for x in [prior_metrics.get(key),performance.get(key)] if x is not None),default=None)
        for key in ['samples','estimated_gpu_energy_joules']:
            values=[x for x in [prior_metrics.get(key),performance.get(key)] if x is not None];performance[key]=sum(values) if values else None
    after=inventory(path/'artifacts');info.update(status='failed' if error else 'finished',generation_status='failed' if error else 'finished',error=error,
        generation_seconds=prior_seconds+elapsed_seconds,performance=performance,finished=now(),
        changes={'added':[p for p in after if p not in before],'changed':[p for p in after if p in before and after[p]!=before[p]],'removed':[p for p in before if p not in after]},
        summary=read_json(path/'agent_state.json',{}).get('final_summary'),stop_reason=read_json(path/'agent_state.json',{}).get('stop_reason'))
    if info.get('prompts'):
        info['prompts'][-1].update(status=info['generation_status'],seconds=(checkpoint['used_seconds'] if checkpoint else 0)+elapsed_seconds,summary=info['summary'],changes=info['changes'],error=error,
            performance={key:(checkpoint.get('prompt_metrics',{}).get(key,0) if checkpoint else 0)+performance[key]-before_calls[key] for key in ['input_tokens','output_tokens','inference_calls','tool_calls','tool_failures']})
    if checkpoint:info.setdefault('resume_history',[]).append({**checkpoint,'finished':now(),'resumed_seconds':elapsed_seconds});info.pop('resume_checkpoint',None)
    event(path,'status',('Revision failed: '+error if error else 'Revision finished. Re-evaluation can be requested separately.')+'\n')
    return info

def score(path,info):
    evaluation_id='eval-'+os.urandom(5).hex();snapshot=path/'evaluations'/evaluation_id;start=time.perf_counter();error=None;scores=None
    (snapshot/'input').mkdir(parents=True);(snapshot/'artifacts').mkdir()
    shutil.copytree(path/'input',snapshot/'input',dirs_exist_ok=True)
    for p in artifact_files(path/'artifacts'):
        target=snapshot/'artifacts'/p.relative_to(path/'artifacts');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    shutil.copy2(path/'identity.json',snapshot/'identity.json')
    if (path/'inference_calls.jsonl').exists():shutil.copy2(path/'inference_calls.jsonl',snapshot/'inference_calls.jsonl')
    event(path,'status','Re-evaluating a snapshot with the original task rubric.\n')
    try:
        with Sandbox(snapshot) as box:
            link_dependencies(box,snapshot)
            scorer=text_detective if info.get('sensory_track')==text_detective.TRACK else SCORERS[info['task']]
            scores=scorer.score(snapshot,box)
    except Exception as e:error=str(e)
    result={'evaluation_id':evaluation_id,'timestamp':now(),'seconds':time.perf_counter()-start,'scores':scores,'error':error,'update_id':info.get('current_update_id'),'rubric':'original benchmark task rubric','snapshot_path':str(snapshot.relative_to(ROOT))}
    write_json(snapshot/'evaluation.json',result);info.setdefault('evaluations',[]).append(result);info['status']=info.get('generation_status','finished')
    event(path,'status',('Re-evaluation failed: '+error if error else 'New score saved separately; original score and revision outputs preserved.')+'\n');return info

def main():
    import psutil
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);parser.add_argument('--operation',choices=['update','score'],required=True);args=parser.parse_args()
    from dashboard.backend.modifications import location
    path=location(args.revision);info=read_json(path/'revision.json');lock=ROOT/'logs'/'gpu-controller.lock';existing=read_json(lock,{})
    if existing and psutil.pid_exists(existing.get('pid',-1)):
        info['status']='queued' if args.operation=='update' else 'queued_score';write_json(path/'revision.json',info);return
    lock.unlink(missing_ok=True)
    try:fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    except FileExistsError:
        info['status']='queued' if args.operation=='update' else 'queued_score';write_json(path/'revision.json',info);return
    with os.fdopen(fd,'w') as f:json.dump({'pid':os.getpid(),'start':now(),'kind':'revision','revision_id':args.revision},f)
    from dashboard.backend.parameters import enrich
    discovered=read_json(ROOT/'models'/'discovered.json',{}).get('models',[])
    recorded=next((m for m in discovered if m['digest']==info['model']['digest']),None)
    if recorded:info['model']=enrich(recorded);info['parameter_estimate_recorded_at']=now()
    info.update(worker_pid=os.getpid(),status='running' if args.operation=='update' else 'reevaluating',operation_start=now(),settings=config()['benchmark'])
    if args.operation=='update' and info.get('prompts'):info['prompts'][-1]['status']='running'
    write_json(path/'revision.json',info)
    try:info=update(path,info) if args.operation=='update' else score(path,info)
    except BaseException as e:
        from dashboard.backend.modifications import elapsed
        seconds=elapsed(info)
        if args.operation=='update':
            info['generation_seconds']=(info.get('generation_seconds',0) if info.get('workspace_mode') else 0)+seconds
            info['generation_status']='failed'
            if info.get('prompts'):info['prompts'][-1].update(status='failed',seconds=seconds,error=str(e) or type(e).__name__)
        else:info.setdefault('evaluations',[]).append({'evaluation_id':'failed-'+os.urandom(5).hex(),'timestamp':now(),'seconds':seconds,'scores':None,'error':str(e) or type(e).__name__,'update_id':info.get('current_update_id')})
        info.update(status='failed',error=str(e) or type(e).__name__);event(path,'status','Operation failed: '+str(e))
    finally:
        info.pop('operation_start',None);write_json(path/'revision.json',info)
        if read_json(lock,{}).get('pid')==os.getpid():lock.unlink(missing_ok=True)

if __name__=='__main__':
    with windows_io.atomic_replacements(ROOT),windows_io.long_file_copies():main()
