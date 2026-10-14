from pathlib import Path
import re, uuid, shutil
from benchmark.util import ROOT, now, write_json

TASK_DIRS = {'data_analysis':'01_data_analysis','racing_game':'02_racing_game','detective':'03_detective'}

def model_folder(model):
    name = re.sub(r'[^a-zA-Z0-9._-]', '-', model['name'])[:100]
    return ROOT/'models'/(name+'--'+model['digest'][:12])

def create_workspace(model, task, case=None):
    run_id = now().replace(':','').replace('.','-')+'--'+uuid.uuid4().hex[:8]
    run = model_folder(model)/TASK_DIRS[task]/run_id
    (run/'artifacts').mkdir(parents=True); (run/'input').mkdir()
    source = ROOT/'datasets'/('data_analysis' if task=='data_analysis' else 'racing_game')
    if task=='detective': source = ROOT/'datasets'/'detective'/case/'public'
    shutil.copytree(source, run/'input', dirs_exist_ok=True)
    write_json(run/'identity.json', {'run_id':run_id,'model':model['name'],'digest':model['digest'],'task':task,'case':case,'created':now()})
    return run
