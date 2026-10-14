import asyncio,json,time,base64,traceback,uuid,httpx
from pathlib import Path
from inspect_ai import Task,eval,task
from inspect_ai.dataset import Sample
from inspect_ai.model import Model,GenerateConfig,ChatMessageSystem,ChatMessageUser,ContentText,ContentImage,get_model,execute_tools
from inspect_ai.solver import solver
from inspect_ai.scorer import scorer,Score,mean
from inspect_ai.tool import tool,ToolCall
from benchmark.util import ROOT,config,now,write_json,append_json,source_hash,read_json,artifact_files
from benchmark.harness.ollama_adapter import OllamaAdapter
from benchmark.harness.workspace_manager import create_workspace
from benchmark.harness.execution_manager import Sandbox,filesystem
from benchmark.harness.resource_monitor import ResourceMonitor
from benchmark.harness.metrics_collector import collect
from benchmark.common_tools.python_executor import execute_python
from benchmark.common_tools.terminal_executor import execute
from benchmark.common_tools.browser_tools import browser_probe
from benchmark.scoring import data_scorer,game_scorer,detective_scorer

PROCESS_PROTOCOL=source_hash()

def live_progress(run,stage,**fields):
    path=ROOT/'logs'/'current_task.json'
    previous=read_json(path,{})
    if previous.get('run_path')!=str(run.relative_to(ROOT)):previous={}
    write_json(path,{**previous,'run_path':str(run.relative_to(ROOT)),'stage':stage,'updated_at':now(),**fields})

PROTOCOL='''
Tool protocol: reply with one JSON object, without markdown, using either an action or {"actions":[...]} (up to four actions).
Actions:
{"tool":"list","path":"/input"}
{"tool":"read","path":"/input/file.csv"}
{"tool":"write","path":"/output/report.md","content":"full file text"}
{"tool":"python","code":"Python source to execute"}
{"tool":"run","command":"bash command, executed inside the isolated Linux container"}
{"tool":"browser"} (builds /output/game, opens Chromium, tests controls, captures screenshots)
{"tool":"view_images","paths":["/input/images/V01.png","/input/images/V02.png"]} (at most two images; actual pixels returned)
{"tool":"finish","summary":"Completed outputs and candid limitations"}
This JSON protocol is the same for every model, including those without native tool calling.
You may attach a "notes" string to any action. Notes are retained in the execution ledger when older messages are compacted. Record concise observations after viewing images or calculating key numbers; do not repeatedly re-read the same evidence. Working notes may also be saved in /output.
Only /input (read-only) and /output (writable) are mounted. Network is disabled. Python has pandas, numpy, matplotlib, plotly, Pillow.
Write large implementations in small modules or append chunks using Python/run. Keep each action comfortably within the output-token budget; an incomplete JSON action cannot be executed.
For games, /output/game contains an infrastructure-only starter; node_modules links to the identical preinstalled Three.js/Vite environment. Never install dependencies. Use npm run build or the browser tool.
Keep tool results concise. Your files persist even when conversation history is compacted. All submissions must be real files in /output.
For data analysis, findings.json must use {"metrics":{"total_revenue":number,"profit_margin":fraction,"clean_row_count":integer,"duplicate_count":integer,"missing_unit_cost":integer,"invalid_quantity_count":integer,"entry_outlier_count":integer},"findings":[{"title":"...","evidence":...,"method":"...","limitations":"...","charts":[...]}]}. State your cleaning rules; include additional metrics if useful. Counts describe raw data issues; financial totals describe cleaned data.
The read tool returns a 4,000-character preview. Do not dump full CSVs: use Python to inspect table shapes/types and calculate concise summaries. Keep stdout concise; returned tool output is limited to 6,000 characters.
Detective conclusions.json should use {"responsible_person": "Full Name" or null, "confidence":0..1, "conclusion":"...", "exhibits":[...]}; evidence_analysis.json and timeline.json should cite exhibit IDs.
For browser diagnostics expose window.__BENCHMARK__ = {snapshot:()=>({selectedCar,playerPosition:[x,y,z],elapsed,camera,npcs:[{laps,collisions,stuck,recoveries}]}), step:(seconds,dt)=>...}. Hooks do not replace independent review.
'''

def parse_actions(text):
    text=text.strip()
    try:obj=json.loads(text)
    except ValueError:
        candidate=text[text.index('{'):].strip()
        if candidate.endswith('```'):candidate=candidate[:-3].strip()
        try:obj=json.loads(candidate)
        except ValueError:
            # Accept only a missing final object delimiter; never invent truncated code.
            obj=json.loads(candidate+'}') if candidate.endswith(('"',']')) else json.loads(candidate[:candidate.rindex('}')+1])
    actions=obj.get('actions',[obj])
    if not isinstance(actions,list) or not 1<=len(actions)<=4:raise ValueError('Provide 1–4 actions')
    for action in actions:
        if not isinstance(action,dict) or action.get('tool') not in ['list','read','write','python','run','browser','view_images','finish']:raise ValueError('Unknown tool or malformed action')
        required={'list':['path'],'read':['path'],'write':['path','content'],'python':['code'],'run':['command'],'finish':['summary']}.get(action['tool'],[])
        if any(not isinstance(action.get(field),str) for field in required):raise ValueError('Required tool arguments must be strings: '+', '.join(required))
    return actions

@tool
def sandbox_dispatch(box, images_pending, model):
    async def dispatch(request: str) -> str:
        """Execute validated JSON actions within the assigned isolated workspace.

        Args:
          request: JSON action object or object containing an actions list.
        """
        results=[]
        for a in parse_actions(request):
            kind=a['tool']
            if kind in ['list','read','write']:
                result=await asyncio.to_thread(filesystem,box,kind,a.get('path','/input'),a.get('content',''))
            elif kind=='python':result=await asyncio.to_thread(execute_python,box,str(a['code']))
            elif kind=='run':result=await asyncio.to_thread(execute,box,str(a['command']))
            elif kind=='browser':result=await asyncio.to_thread(browser_probe,box)
            elif kind=='view_images':
                if not model['vision']:raise ValueError('Model does not support native images')
                paths=a.get('paths',[])
                if not isinstance(paths,list) or not 1<=len(paths)<=2:raise ValueError('Use one or two image paths')
                for path in paths:
                    rel=Path(str(path).removeprefix('/input/'))
                    full=(box.run/'input'/rel).resolve()
                    if not str(path).startswith('/input/') or not full.is_relative_to((box.run/'input').resolve()) or full.suffix.lower() not in ['.png','.jpg','.jpeg']:raise ValueError('Invalid image input path')
                    images_pending.append((str(path),full.read_bytes()))
                result={'images':paths,'note':'Actual image pixels will follow as multimodal content.'}
                append_json(box.run/'tool_calls.jsonl',{'category':'image_read','command':paths,'exit_code':0,'duration_seconds':0,'start':now(),'end':now()})
            else:result={'finished':True,'summary':a.get('summary','')}
            results.append({'tool':kind,'result':result})
        result_text=json.dumps(results,ensure_ascii=False)
        return result_text[:6000]+('\n[Tool result truncated; files and full execution logs are retained.]' if len(result_text)>6000 else '')
    return dispatch

@solver
def local_agent(box, model, deadline, run, max_calls):
    async def solve(state,generate):
        pending=[];dispatch=sandbox_dispatch(box,pending,model);initial=list(state.messages);transcript=[]
        for turn in range(max_calls):
            if time.perf_counter()>=deadline:state.metadata['stop_reason']='time_budget';break
            # Keep the fixed instructions, latest four interactions, and a small factual execution ledger.
            visible_chars=sum(len(m.content) if isinstance(m.content,str) else sum(len(getattr(c,'text','')) for c in m.content) for m in state.messages)
            image_messages=sum(sum(getattr(c,'type','')=='image' for c in m.content) if isinstance(m.content,list) else 0 for m in state.messages)
            if len(state.messages)>50 or visible_chars>60000 or image_messages>14:
                ledger='Prior executed actions (files remain on disk):\n'+'\n'.join(transcript[-12:])
                state.messages=initial+[ChatMessageUser(content=ledger)]+list(state.messages[-4:])
                append_json(run/'execution_trace.jsonl',{'event':'context_compaction','turn':turn,'timestamp':now(),'method':'fixed initial instructions + execution ledger + last four messages'})
            files=[]
            for p in artifact_files(run/'artifacts'):
                files.append(str(p.relative_to(run/'artifacts')))
                if len(files)>=80:break
            reminder=f'Controller budget: call {turn+1}/{max_calls}; {max_calls-turn-1} calls remain after this one; {max(0,int(deadline-time.perf_counter()))} seconds left. Actual output files so far: {files}. '
            if max_calls-turn<=5:reminder+='Prioritize writing the required submission files now. Save partial supported results and candid limitations if needed.'
            state.messages.append(ChatMessageUser(content=reminder))
            live_progress(run,'Model inference',call=turn+1,completed_calls=turn)
            state.output=await get_model().generate(state.messages)
            message=state.output.choices[0].message;state.messages.append(message)
            text=state.output.completion
            append_json(run/'execution_trace.jsonl',{'event':'assistant','turn':turn,'timestamp':now(),'content':text})
            try:
                actions=parse_actions(text)
                message.tool_calls=[ToolCall(id=uuid.uuid4().hex,function='sandbox_dispatch',arguments={'request':json.dumps({'actions':actions})})]
                live_progress(run,'Executing tools',call=turn+1,completed_calls=turn+1)
                result=await execute_tools([message],[dispatch],max_output=7000)
                state.messages.extend(result.messages)
                for reply in result.messages:
                    append_json(run/'execution_trace.jsonl',{'event':'tool_result','timestamp':now(),'turn':turn,'content':reply.content,'error':str(getattr(reply,'error','') or '')})
                    if getattr(reply,'error',None):append_json(run/'tool_calls.jsonl',{'category':'tool_dispatch_error','command':text[:2000],'exit_code':1,'stderr':str(reply.error),'duration_seconds':0,'start':now(),'end':now()})
                transcript.extend(json.dumps({k:v for k,v in a.items() if k not in ['content','code']})[:400] for a in actions)
                for label,data in pending:
                    state.messages.append(ChatMessageUser(content=[ContentText(text='Native visual exhibit: '+label),ContentImage(image='data:image/png;base64,'+base64.b64encode(data).decode())]))
                pending.clear()
                if any(a['tool']=='finish' for a in actions):
                    state.metadata['stop_reason']='model_finish';state.metadata['final_summary']=text;break
            except Exception as e:
                append_json(run/'tool_calls.jsonl',{'category':'invalid_arguments','command':text[:2000],'exit_code':1,'stderr':str(e),'duration_seconds':0,'start':now(),'end':now()})
                guidance=' The model reached its output limit: split the code into smaller files or append chunks; the truncated action was not executed.' if state.output.choices[0].stop_reason=='max_tokens' else ''
                state.messages.append(ChatMessageUser(content='Tool protocol error: '+str(e)+'. Return valid JSON. Files must be created through tools; prose alone is not a submission.'+guidance))
        else:state.metadata['stop_reason']='call_budget'
        write_json(run/'agent_state.json',{'stop_reason':state.metadata.get('stop_reason'),'final_summary':state.metadata.get('final_summary'),'iterations':turn+1})
        state.completed=True
        return state
    return solve

SCORERS={'data_analysis':data_scorer,'racing_game':game_scorer,'detective':detective_scorer}

@scorer(metrics=[mean()])
def artifact_score(run,box,kind):
    async def score(state,target):
        live_progress(run,'Scoring and validation')
        start=time.perf_counter()
        result=await asyncio.to_thread(SCORERS[kind].score,run,box)
        result['scoring_seconds']=time.perf_counter()-start
        write_json(run/'scores.json',result)
        return Score(value=result['verified_points']/100,explanation='Verified automatic points; pending human rubric excluded.',metadata=result)
    return score

def make_task(kind,run,box,model,deadline):
    cfg=config()['benchmark'];system=(ROOT/'benchmark'/'prompts'/'common_system_prompt.md').read_text(encoding='utf-8')
    prompt=(ROOT/'benchmark'/'prompts'/(kind+'_prompt.md')).read_text(encoding='utf-8')
    listing='\n'.join(str(p.relative_to(run/'input')) for p in (run/'input').rglob('*') if p.is_file())
    extra=f'\n\nBudget: {cfg["max_calls"]} model calls, {cfg["max_output_tokens_per_call"]} output tokens per call, {cfg["task_timeout_seconds"]} seconds.\nInput files:\n{listing}\n'
    if kind=='detective':
        extra+=(run/'input'/'case_brief.md').read_text(encoding='utf-8')
        for doc in sorted((run/'input'/'documents').glob('*')):extra+='\n\nPUBLIC DOCUMENT '+doc.name+'\n'+doc.read_text(encoding='utf-8')
        content=[ContentText(text=prompt+extra)]
        for p in [run/'input'/'images'/'V01.png',run/'input'/'images'/'V02.png']:
            content.extend([ContentText(text='Native visual exhibit '+p.name),ContentImage(image='data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode())])
        user=ChatMessageUser(content=content)
    else:user=ChatMessageUser(content=prompt+extra)
    sample=Sample(id='attempt',input=[ChatMessageSystem(content=system+'\n'+PROTOCOL),user])
    return Task(name='local_'+kind,version=1,dataset=[sample],solver=local_agent(box,model,deadline,run,cfg['max_calls']),scorer=artifact_score(run,box,kind),
        metadata={'benchmark_version':cfg['version'],'protocol_hash':PROCESS_PROTOCOL,'run_path':str(run)},time_limit=cfg['task_timeout_seconds']+300)

def run_attempt(model,kind,case=None,repetition=1,pilot=True):
    if source_hash()!=PROCESS_PROTOCOL:raise RuntimeError('Benchmark source/config/dataset changed while controller was running. Restart with the same command; immutable previous attempts are retained.')
    attempt_config=config();cfg=attempt_config['benchmark'];protocol=PROCESS_PROTOCOL;run=create_workspace(model,kind,case);started=now();start=time.perf_counter();monitor=ResourceMonitor(run).start()
    live_progress(run,'Preparing sandbox',model=model['name'],task=kind,case=case,start=started,limit_seconds=cfg['task_timeout_seconds'],max_calls=cfg['max_calls'],completed_calls=0,active=True)
    status='failed';error=None;setup_seconds=None;inspect_status=None
    try:
        with httpx.Client(timeout=60) as client:client.post(cfg['base_url']+'/api/generate',json={'model':model['name'],'keep_alive':0})
        with Sandbox(run) as box:
            if kind=='racing_game':box.exec(['bash','-lc','cp -r /input/game /output/game && ln -s /opt/lab/node_modules /output/game/node_modules'],category='environment_setup')
            setup_seconds=time.perf_counter()-start;deadline=time.perf_counter()+cfg['task_timeout_seconds']
            live_progress(run,'Model inference',inference_start=now())
            adapter=OllamaAdapter(model,run,deadline);instance=Model(adapter,GenerateConfig(max_tokens=cfg['max_output_tokens_per_call'],temperature=0,max_connections=1,max_retries=0))
            # Inspect log filenames exceed legacy Windows MAX_PATH under OneDrive.
            logdir=Path('D:/LocalLLM/benchmark-inspect-logs')/read_json(run/'identity.json')['run_id'].rsplit('--',1)[-1]
            logdir.mkdir(parents=True,exist_ok=True)
            write_json(run/'inspect_logs.json',{'directory':str(logdir)})
            logs=eval(make_task(kind,run,box,model,deadline),model=instance,log_dir=str(logdir),display='none',max_samples=1,max_tasks=1,log_images=False,score_on_error=True,fail_on_error=False)
            inspect_status=logs[0].status;status='evaluated' if inspect_status=='success' else 'failed'
            if logs[0].error:error=logs[0].error.message
            sample_errors=[s.error for s in (logs[0].samples or []) if s.error]
            if sample_errors:
                status='failed';error=sample_errors[0].message
                write_json(run/'inspect_sample_errors.json',[e.model_dump() for e in sample_errors])
    except Exception as e:
        error=f'{type(e).__name__}: {e}';(run/'error.txt').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        monitor.stop()
        try:
            with httpx.Client(timeout=30) as client:
                ps=client.get(cfg['base_url']+'/api/ps').json().get('models',[])
                residency=next(({'size':m.get('size'),'size_vram':m.get('size_vram'),'context_length':m.get('context_length')} for m in ps if m['name']==model['name']),None)
                client.post(cfg['base_url']+'/api/generate',json={'model':model['name'],'keep_alive':0})
        except Exception:residency=None
    scores=read_json(run/'scores.json')
    if not scores:
        try:scores=SCORERS[kind].score(run)
        except Exception as e:scores={'verified_points':0,'pending_points':100,'quality_score':None,'complete':False,'scoring_error':str(e)}
        write_json(run/'scores.json',scores)
    perf={**collect(run),**monitor.summary(),'environment_setup_seconds':setup_seconds,'scoring_seconds':scores.get('scoring_seconds'),
        'figure_generation_seconds':None,'report_generation_seconds':None,'artifact_count':sum(1 for p in artifact_files(run/'artifacts')),
        'stop_reason':read_json(run/'agent_state.json',{}).get('stop_reason', 'harness_error' if error else 'unknown')}
    write_json(run/'performance.json',perf)
    identity=read_json(run/'identity.json');value={**identity,'model':{k:v for k,v in model.items() if k!='show'},'start':started,'end':now(),
        'task_seconds':time.perf_counter()-start,'status':status,'error':error,'inspect_status':inspect_status,'pilot':pilot,'repetition':repetition,
        'benchmark_version':cfg['version'],'protocol_hash':protocol,'config':attempt_config,'scores':scores,'performance':perf,
        'run_path':str(run.relative_to(ROOT)),'residency':residency,'sensory_track':'native_multimodal' if kind=='detective' else 'text_and_tools',
        'docker_image_id':__import__('subprocess').run(['docker','image','inspect',config()['sandbox']['image'],'--format','{{.Id}}'],capture_output=True,text=True).stdout.strip()}
    write_json(run/'result.json',value)
    live_progress(run,'Finished',active=False,status=status)
    print(f'{model["name"]} {kind} {case or ""}: {status}; verified={scores.get("verified_points")}; complete={scores.get("complete")}; {value["task_seconds"]:.1f}s',flush=True)
    return value
