"""Expose the existing sandbox actions through GPT-OSS's native function channel.

This changes transport, not the sandbox, tasks, budgets or scoring. The distinct
protocol hash and raw native calls make the compatibility change inspectable.
"""
import hashlib,json,time
from pathlib import Path
from contextlib import asynccontextmanager
from unittest.mock import patch
import httpx
from benchmark.util import append_json,write_json,now
from benchmark.harness.ollama_adapter import OllamaAdapter
from inspect_ai.model import ModelOutput,ChatCompletionChoice,ChatMessageAssistant,ContentText

SOURCE=Path(__file__).read_bytes()

INSTRUCTION='\nTransport override: The JSON protocol examples describe sandbox actions. Submit them using the provided bench_* functions: bench_list, bench_read, bench_write, bench_python, bench_run, bench_browser, bench_view_images and bench_finish. These expose exactly the same eight actions. Pass the fields directly to the matching function; there is no tool-name field or actions wrapper in function arguments. Do not send action JSON as prose and do not call native python, container.exec or browser tools. You may submit up to four bench_* calls per response. Finish with bench_finish.'

FIELDS={'tool':{'type':'string','enum':['list','read','write','python','run','browser','view_images','finish']},
    **{k:{'type':'string'} for k in ['path','content','code','command','summary','notes']},'paths':{'type':'array','items':{'type':'string'}}}
ACTION_FIELDS={'list':['path'],'read':['path'],'write':['path','content'],'python':['code'],'run':['command'],'browser':[],'view_images':['paths'],'finish':['summary']}
DESCRIPTIONS={'list':'List files under an /input or /output path.','read':'Read a text file in /input or /output.','write':'Save complete text content to a file under /output.','python':'Execute Python source code in the isolated sandbox, with pandas/numpy/matplotlib. Save outputs under /output.','run':'Run a Linux shell command inside the isolated sandbox.','browser':'Build and probe the game under /output/game, and capture screenshots.','view_images':'Inspect up to two provided image paths.','finish':'Finish this attempt with a concise summary of the actual saved outputs and limitations.'}
TOOLS=[{'type':'function','function':{'name':'bench_'+action,'description':DESCRIPTIONS[action],
    'parameters':{'type':'object','properties':{k:FIELDS[k] for k in fields},'required':fields}}} for action,fields in ACTION_FIELDS.items()]

def protocol(base):return hashlib.sha256(base.encode()+SOURCE).hexdigest()

def translate(calls):
    actions=[]
    for call in calls:
        function=call.get('function',{})
        name=function.get('name','')
        action=name[6:] if name.startswith('bench_') else None
        if name!='sandbox_dispatch' and action not in ACTION_FIELDS:
            actions.append({'tool':'unsupported_native_tool','notes':'Use the provided bench_* functions. Requested: '+str(function.get('name'))});continue
        arguments=function.get('arguments',{})
        try:
            arguments=json.loads(arguments) if isinstance(arguments,str) else arguments
            actions.append({**arguments,'tool':action} if action and isinstance(arguments,dict) else arguments)
        except ValueError:actions.append({'tool':'invalid_native_arguments','notes':'Pass valid JSON fields directly to a bench_* function.'})
    # The ordinary solver validates every action before executing it. Invalid
    # arguments become feedback to the model, consuming the same call budget.
    return json.dumps({'actions':actions})

def bridge_client(run):
    original=httpx.AsyncClient
    class Response:
        def __init__(self,response):self.response=response
        def __getattr__(self,name):return getattr(self.response,name)
        def raise_for_status(self):
            if self.response.status_code>=400 and 'error parsing tool call' in self.response.text:raise RuntimeError(self.response.text)
            return self.response.raise_for_status()
        async def aiter_lines(self):
            calls=[]
            async for line in self.response.aiter_lines():
                if not line:yield line;continue
                chunk=json.loads(line);message=chunk.get('message',{})
                if message.get('tool_calls'):
                    calls.extend(message['tool_calls'])
                    append_json(run/'native_tool_calls.jsonl',{'timestamp':now(),'calls':message['tool_calls']})
                if chunk.get('done') and calls:
                    message['content']=translate(calls);chunk['message']=message
                yield json.dumps(chunk)
    class Client(original):
        @asynccontextmanager
        async def stream(self,*args,**kwargs):
            payload=kwargs.get('json')
            if payload and payload.get('model','').startswith('gpt-oss:'):
                payload['tools']=TOOLS
                for message in payload['messages']:
                    if message['role']=='system':message['content']+=INSTRUCTION;break
            async with super().stream(*args,**kwargs) as response:
                if response.status_code>=400:await response.aread()
                yield Response(response)
    return Client

def adapter(model,run,deadline):
    instance=OllamaAdapter(model,run,deadline)
    if not model['name'].startswith('gpt-oss:'):return instance
    generate=instance.generate
    async def native_generate(*args,**kwargs):
        write_json(run/'transport_compatibility.json',{'transport':'GPT-OSS native sandbox action bridge','instruction':INSTRUCTION,'tools':TOOLS,'source_sha256':hashlib.sha256(SOURCE).hexdigest(),
            'native_reasoning':'unchanged default','task_budget':'unchanged','sandbox_actions':'same validation and dispatch','timestamp':now()})
        with patch('benchmark.harness.ollama_adapter.httpx.AsyncClient',bridge_client(run)):
            try:return await generate(*args,**kwargs)
            except RuntimeError as error:
                if 'error parsing tool call' not in str(error):raise
                # The failed call was already logged with success=False, actual
                # elapsed time, and unavailable token counters. Do not fabricate
                # duration/token values or make an extra hidden model request.
                append_json(run/'native_transport_errors.jsonl',{'timestamp':now(),'error':str(error),'call':instance.calls,'recovery':'Feedback on the next ordinary solver iteration'})
                text=json.dumps({'tool':'invalid_native_tool_call','notes':'Native call parsing failed. Use a bench_* function with short, valid JSON fields; split large code into smaller writes.'})
                return ModelOutput(model=model['name'],choices=[ChatCompletionChoice(message=ChatMessageAssistant(content=[ContentText(text=text)]),stop_reason='stop')],metadata={'native_parse_error':str(error),'token_counters':'unavailable'})
    instance.generate=native_generate
    return instance
