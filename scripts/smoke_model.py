import _bootstrap,time,uuid
from benchmark.util import ROOT,write_json
from benchmark.harness.model_discovery import discover
from benchmark.harness.execution_manager import Sandbox
from benchmark.harness.runner import local_agent,PROTOCOL
from benchmark.harness.ollama_adapter import OllamaAdapter
from inspect_ai import Task,eval
from inspect_ai.dataset import Sample
from inspect_ai.model import Model,GenerateConfig,ChatMessageSystem,ChatMessageUser

def main():
    model=next(m for m in discover() if m['name']=='gemma4:12b-it-q4_K_M')
    run=ROOT/'logs'/('model-smoke-'+uuid.uuid4().hex[:8]);(run/'input').mkdir(parents=True);(run/'artifacts').mkdir()
    with Sandbox(run) as box:
        deadline=time.perf_counter()+300
        adapter=OllamaAdapter(model,run,deadline)
        t=Task(name='lab_smoke',dataset=[Sample(input=[ChatMessageSystem(content=PROTOCOL),ChatMessageUser(content='Create /output/smoke.txt containing sandbox ok using the write tool, read it back, then finish. This is a tools smoke check, not a benchmark task.')])],solver=local_agent(box,model,deadline,run,3))
        logs=eval(t,model=Model(adapter,GenerateConfig(max_tokens=1024,max_connections=1,max_retries=0)),display='none',log_dir=str(run/'inspect_logs'))
        success=(run/'artifacts'/'smoke.txt').exists() and (run/'artifacts'/'smoke.txt').read_text()=='sandbox ok' and logs[0].status=='success'
    write_json(ROOT/'results'/'model_smoke.json',{'success':success,'run_path':str(run.relative_to(ROOT)),'inspect_status':logs[0].status})
    if not success:raise RuntimeError(f'Model smoke failed: {run}')
    print('Inspect + streaming Ollama + tool execution smoke passed.')
if __name__=='__main__':main()
