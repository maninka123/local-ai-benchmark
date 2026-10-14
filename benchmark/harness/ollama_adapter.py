"""Inspect ModelAPI extension using native streaming /api/chat statistics."""
import httpx,json,time,base64
from inspect_ai.model import ModelAPI,ModelOutput,ChatCompletionChoice,ChatMessageAssistant,ModelUsage,ContentText,ContentReasoning,modelapi
from benchmark.util import config,append_json,now

@modelapi('local_ollama_stats')
class OllamaAdapter(ModelAPI):
    def __init__(self, model, run, deadline):
        cfg=config()['benchmark'];super().__init__(model['name'],base_url=cfg['base_url'])
        self.identity=model;self.run=run;self.deadline=deadline;self.calls=0;self.cfg=cfg
    async def generate(self,input,tools,tool_choice,config):
        self.calls+=1; messages=[];image_count=0
        for msg in input:
            content=msg.content; text=content if isinstance(content,str) else '\n'.join(c.text for c in content if getattr(c,'type','')=='text')
            item={'role':'user' if msg.role=='tool' else msg.role,'content':('Tool result:\n' if msg.role=='tool' else '')+text}
            if isinstance(content,list):
                images=[]
                for c in content:
                    if getattr(c,'type','')=='image':
                        url=c.image
                        if url.startswith('data:'):images.append(url.split(',',1)[1])
                        else:raise ValueError('Only explicit data image inputs supported; no network fetching')
                if images:item['images']=images;image_count+=len(images)
            messages.append(item)
        remaining=max(1,self.deadline-time.perf_counter());max_tokens=config.max_tokens or self.cfg['max_output_tokens_per_call']
        payload={'model':self.model_name,'messages':messages,'stream':True,'keep_alive':'10m',
            'options':{'temperature':self.cfg['temperature'],'num_ctx':self.cfg['context_window'],'num_predict':max_tokens,'seed':self.cfg['seed'],'num_thread':16}}
        # Native default reasoning is retained: think is deliberately not set.
        start=time.perf_counter();started=now();text='';reason='';first=None;first_visible=None;last={};error=None
        append_json(self.run/'execution_trace.jsonl',{'event':'inference_start','call':self.calls,'timestamp':started,'image_count':image_count,'options':payload['options'],'reasoning':'native default'})
        try:
            import asyncio
            async with asyncio.timeout(remaining) if hasattr(asyncio,'timeout') else _timeout(remaining):
                async with httpx.AsyncClient(timeout=httpx.Timeout(remaining,connect=15)) as client:
                    async with client.stream('POST',self.base_url+'/api/chat',json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line:continue
                            chunk=json.loads(line)
                            if chunk.get('error'):raise RuntimeError(chunk['error'])
                            m=chunk.get('message',{});piece=m.get('content','');thinking=m.get('thinking','')
                            if (piece or thinking) and first is None:first=time.perf_counter()-start
                            if piece and first_visible is None:first_visible=time.perf_counter()-start
                            text+=piece;reason+=thinking
                            if chunk.get('done'):last=chunk
            if not last:raise RuntimeError('Stream ended without final Ollama statistics')
        except Exception as e:error=f'{type(e).__name__}: {e}'
        duration=time.perf_counter()-start
        p=last.get('prompt_eval_count');g=last.get('eval_count');pd=last.get('prompt_eval_duration');gd=last.get('eval_duration')
        record={'call':self.calls,'model':self.model_name,'digest':self.identity['digest'],'start':started,'end':now(),'success':error is None,'error':error,
            'input_tokens':p,'output_tokens':g,'total_tokens':p+g if p is not None and g is not None else None,
            'prompt_eval_duration_ns':pd,'eval_duration_ns':gd,'load_duration_ns':last.get('load_duration'),'total_duration_ns':last.get('total_duration'),
            'prompt_tokens_per_second':p/(pd/1e9) if p is not None and pd else None,'generation_tokens_per_second':g/(gd/1e9) if g is not None and gd else None,
            'ttft_seconds':first,'first_visible_token_seconds':first_visible,'wall_seconds':duration,'image_count':image_count,
            'reasoning_tokens':None,'reasoning_characters':len(reason),'reasoning_mode':'native default','stop_reason':last.get('done_reason'),
            'content':text,'thinking':reason,'request_messages':messages,'options':payload['options']}
        # Separate image payloads from JSONL to keep traces inspectable; inputs retain originals.
        record['request_messages']=[{**m,'images':[f'[base64 image {len(x)} chars]' for x in m['images']]} if 'images' in m else m for m in messages]
        append_json(self.run/'inference_calls.jsonl',record)
        if error:raise RuntimeError(error)
        parts=[]
        if reason:parts.append(ContentReasoning(reasoning=reason))
        parts.append(ContentText(text=text))
        return ModelOutput(model=self.model_name,choices=[ChatCompletionChoice(message=ChatMessageAssistant(content=parts),stop_reason='max_tokens' if last.get('done_reason')=='length' else 'stop')],
            usage=ModelUsage(input_tokens=p or 0,output_tokens=g or 0,total_tokens=(p or 0)+(g or 0)),time=duration,metadata={'ollama':{k:v for k,v in last.items() if k!='message'}})

class _timeout:
    """Python 3.10 equivalent of asyncio.timeout, cancelling the task at deadline."""
    def __init__(self,seconds):self.seconds=seconds
    async def __aenter__(self):
        import asyncio
        self.task=asyncio.current_task();self.timer=asyncio.get_running_loop().call_later(self.seconds,self.task.cancel)
    async def __aexit__(self,t,e,tb):
        import asyncio
        self.timer.cancel()
        if t is asyncio.CancelledError:raise TimeoutError('Task inference deadline exceeded')
