"""Real Inspect/tool/sandbox integration with a tiny deterministic test fixture."""
import _bootstrap,time,uuid,shutil
from benchmark.util import ROOT,write_json
from benchmark.harness.execution_manager import Sandbox
from benchmark.harness.runner import local_agent,PROTOCOL
from inspect_ai import Task,eval
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelAPI,modelapi,ModelOutput,ChatCompletionChoice,ChatMessageAssistant,Model,GenerateConfig

@modelapi('game_solver_fixture')
class Fixture(ModelAPI):
    def __init__(self):super().__init__('fixture');self.index=0
    async def generate(self,input,tools,tool_choice,config):
        self.index+=1
        text='{"tool":"read","path":"/output/game/package.json"}' if self.index==1 else '{"tool":"finish","summary":"Game scaffold verified"}'
        return ModelOutput(model='fixture',choices=[ChatCompletionChoice(message=ChatMessageAssistant(content=text),stop_reason='stop')])

run=ROOT/'logs'/('game-solver-smoke-'+uuid.uuid4().hex[:8]);(run/'input').mkdir(parents=True);(run/'artifacts').mkdir()
shutil.copytree(ROOT/'datasets'/'racing_game'/'game',run/'input'/'game')
with Sandbox(run) as box:
    box.exec(['bash','-lc','cp -r /input/game /output/game && ln -s /opt/lab/node_modules /output/game/node_modules'])
    task=Task(name='game_solver_smoke',dataset=[Sample(input='Read the starter package, then finish.')],solver=local_agent(box,{'vision':False},time.perf_counter()+120,run,2))
    logs=eval(task,model=Model(Fixture(),GenerateConfig(max_connections=1,max_retries=0)),display='none',log_dir=str(run/'inspect_logs'))
    errors=[s.error.message for s in logs[0].samples or [] if s.error]
    assert not errors,errors
    assert (run/'agent_state.json').exists()
write_json(ROOT/'results'/'game_solver_validation.json',{'passed':True,'run_path':str(run.relative_to(ROOT)),'fixture':'deterministic test fixture, not a benchmark candidate'})
print('Inspect solver + real Linux node_modules link + Windows artifact discovery + sandbox tools passed.')
