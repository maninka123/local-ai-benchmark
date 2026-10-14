"""Let the in-flight task save its result, then migrate the remaining queue."""
import _bootstrap,sys,time,os,psutil,shutil
from benchmark.util import ROOT,read_json,write_json,now,source_hash,config

def main():
    baseline=sys.argv[1];old_pid=int(sys.argv[2]);lock=ROOT/'logs'/'gpu-controller.lock'
    print(f'Waiting for in-flight controller {old_pid} to finish its current task.',flush=True)
    while psutil.pid_exists(old_pid) and read_json(lock,{}).get('pid')==old_pid:time.sleep(5)
    # The old controller has saved the active attempt and stopped at its source guard.
    cfg_path=ROOT/'config.yaml';text=cfg_path.read_text(encoding='utf-8')
    cfg_path.write_text(text.replace('task_timeout_seconds: 1800','task_timeout_seconds: 3600'),encoding='utf-8')
    for proc in psutil.process_iter(['pid','cmdline','cwd']):
        command=proc.info['cmdline'] or []
        if proc.info['cwd'] and os.path.normcase(proc.info['cwd'])==os.path.normcase(str(ROOT)) and any(x.replace('\\','/').endswith('scripts/watch_results.py') for x in command) and any('python' in x.lower() for x in command):
            try:proc.terminate();proc.wait(timeout=10)
            except (psutil.NoSuchProcess,psutil.TimeoutExpired):pass
    protocol=source_hash();snapshot=ROOT/'logs'/'protocol-snapshots'/protocol;snapshot.mkdir(parents=True,exist_ok=True)
    for name in ['benchmark','scripts','sandbox']:
        shutil.copytree(ROOT/name,snapshot/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','node_modules'))
    for name in ['config.yaml','requirements.txt']:shutil.copy2(ROOT/name,snapshot/name)
    write_json(ROOT/'results'/'validated_protocol.json',{'timestamp':now(),'protocol_hash':protocol,'baseline_protocol':baseline,'config':config(),
        'tests':'9 pytest checks passed; TypeScript/Vite build passed; dashboard browser checks recorded separately.',
        'change':'User requested a 3600-second task deadline, retained prior completed attempts, and end-of-queue timeout retries.'})
    print(f'Launching one-hour continuation under {protocol}.',flush=True)
    os.environ['LLMB_START_OBSERVER']='1'
    sys.argv=['run_extended_pilot.py','--baseline',baseline]
    from run_extended_pilot import main as run
    run()

if __name__=='__main__':main()
