"""Dependency checks and sandbox smoke only; never starts the full benchmark."""
import _bootstrap,subprocess,sys,uuid,shutil
from benchmark.util import ROOT,write_json,config,now
from benchmark.harness.model_discovery import discover,environment
from benchmark.harness.execution_manager import Sandbox,filesystem
from generate_data import main as generate

def main():
    for directory in ['results','logs','evaluation_private/scoring_config','evaluation_private/reference_solutions','models/generated_dynamically']: (ROOT/directory).mkdir(parents=True,exist_ok=True)
    subprocess.run(['docker','info'],check=True,capture_output=True)
    if subprocess.run(['docker','image','inspect',config()['sandbox']['image']],capture_output=True).returncode:
        subprocess.run(['docker','build','-t',config()['sandbox']['image'],str(ROOT/'sandbox')],check=True)
    environment();models=discover();generate()
    path=ROOT/'logs'/('sandbox-smoke-'+uuid.uuid4().hex[:8]);(path/'input').mkdir(parents=True);(path/'artifacts').mkdir()
    (path/'input'/'sentinel.txt').write_text('read-only input',encoding='utf-8')
    with Sandbox(path) as box:
        checks={}
        checks['input_read']=filesystem(box,'read','/input/sentinel.txt')['exit_code']==0
        checks['output_write']=filesystem(box,'write','/output/ok.txt','test')['exit_code']==0
        checks['input_write_blocked']=box.exec(['bash','-lc','echo bad > /input/sentinel.txt'])['exit_code']!=0
        checks['host_private_not_mounted']=box.exec(['python','-c',"import pathlib;assert not pathlib.Path('/evaluation_private').exists(); assert not pathlib.Path('/models').exists(); assert not pathlib.Path('/var/run/docker.sock').exists()"] )['exit_code']==0
        checks['network_blocked']=box.exec(['python','-c',"import socket; socket.create_connection(('1.1.1.1',443),timeout=2)"])['exit_code']!=0
        checks['path_traversal_blocked']=filesystem(box,'read','/input/../../etc/passwd')['exit_code']!=0
        checks['resources']=box.exec(['python','-c',"import pathlib;print(pathlib.Path('/sys/fs/cgroup/memory.max').read_text());print(pathlib.Path('/sys/fs/cgroup/cpu.max').read_text())"])['exit_code']==0
        checks['browser']=box.exec(['node','--input-type=module','-e',"import {chromium} from '/opt/lab/node_modules/playwright/index.mjs'; const b=await chromium.launch({args:['--no-sandbox']});const p=await b.newPage();await p.setContent('<h1>Smoke</h1>');console.log(await p.textContent('h1'));await b.close();"],category='browser_testing')['exit_code']==0
    write_json(ROOT/'results'/'setup_validation.json',{'timestamp':now(),'models':len(models),'checks':checks,'all_passed':all(checks.values()),'trace':str(path.relative_to(ROOT))})
    if not all(checks.values()):raise RuntimeError('Setup validation failed: '+str(checks))
    print('Setup validation passed. No benchmark was automatically started.')
if __name__=='__main__':main()
