"""Enforce isolation in Docker; never fall back to a host shell."""
import subprocess, uuid, time, json
from benchmark.util import config, append_json, now

class Sandbox:
    def __init__(self, run):
        self.run=run; self.name='llmb-'+uuid.uuid4().hex[:16]; self.cfg=config()['sandbox']
    def start(self):
        args=['docker','run','-d','--name',self.name,'--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit',str(self.cfg['pids']),
            '--memory',self.cfg['memory'],'--cpus',str(self.cfg['cpus']),
            '--user','1000:1000','--tmpfs','/tmp:rw,nosuid,nodev,size=512m,mode=1777',
            '--mount',f'type=bind,source={self.run / "input"},target=/input,readonly',
            '--mount',f'type=bind,source={self.run / "artifacts"},target=/output',
            '--workdir','/output','-e','HOME=/tmp','-e','MPLCONFIGDIR=/tmp/mpl',
            self.cfg['image'],'sleep','infinity']
        p=subprocess.run(args,capture_output=True,text=True,timeout=120)
        if p.returncode: raise RuntimeError('Sandbox startup: '+p.stderr)
        return self
    def exec(self, command, stdin=None, timeout=None, category='code_execution'):
        start=time.perf_counter(); t=now()
        timeout=min(timeout or self.cfg['command_timeout_seconds'],self.cfg['command_timeout_seconds'])
        args=['docker','exec','-i',self.name]+command
        try:
            p=subprocess.run(args,input=stdin,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
            result={'exit_code':p.returncode,'stdout':p.stdout[-20000:],'stderr':p.stderr[-10000:]}
        except subprocess.TimeoutExpired:
            # Kill lingering processes by destroying the isolated container, then restart it.
            self.stop(); self.start()
            result={'exit_code':124,'stdout':'','stderr':f'Command exceeded {timeout}s; container restarted.'}
        result.update(duration_seconds=time.perf_counter()-start,category=category,start=t,end=now(),command=command)
        append_json(self.run/'tool_calls.jsonl',result)
        return result
    def stop(self):
        subprocess.run(['docker','rm','-f',self.name],capture_output=True,timeout=60)
    def __enter__(self): return self.start()
    def __exit__(self,*args): self.stop()

PATH_SCRIPT = '''import pathlib,sys,json
p=pathlib.Path(sys.argv[2]).resolve()
allowed=[pathlib.Path('/input'),pathlib.Path('/output')]
if not any(p==a or a in p.parents for a in allowed): raise PermissionError('Path must be in /input or /output')
action=sys.argv[1]
if action=='write':
 if not (p==allowed[1] or allowed[1] in p.parents): raise PermissionError('Inputs are read-only')
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(sys.stdin.read(),encoding='utf-8'); print('Written',p)
elif action=='read':
 text=p.read_text(encoding='utf-8');print(text[:4000]);print('[Preview truncated; use Python to inspect large data.]' if len(text)>4000 else '')
elif action=='list': print('\\n'.join(str(x) for x in sorted(p.rglob('*')) if 'node_modules' not in x.parts)[:4000])
'''

def filesystem(box, action, path, content=''):
    return box.exec(['python','-c',PATH_SCRIPT,action,path],stdin=content,category='filesystem')
