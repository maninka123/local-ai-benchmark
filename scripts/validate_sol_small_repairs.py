import json, subprocess, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'results/improvement_campaign/pass_2/campaign.json').read_text())
for e in c['entries']:
 if len(sys.argv)>1 and e['model'] not in sys.argv[1:]:continue
 d=Path('\\\\?\\'+str(Path(e['further_folder']).parent/'repairs/sol-6.1-small-fix-20261014'))
 p=d/'repair.json'
 if not p.exists():continue
 m=json.loads(p.read_text()); out=d/'artifacts'; source=Path(m['source_artifacts_path'])
 numstat=[];count=0
 for f in m['source_files']:
  r=subprocess.run(['git','-c','core.longpaths=true','diff','--no-index','--numstat','--',str(source/f['path']).removeprefix('\\\\?\\'),str(out/f['path']).removeprefix('\\\\?\\')],capture_output=True,text=True)
  assert r.returncode in (0,1),r.stderr
  for row in r.stdout.splitlines():
   a,b,*_=row.split('\t');count+=int(a)+int(b);numstat.append(row)
  assert hashlib.sha256((source/f['path']).read_bytes()).hexdigest()==m['source_hashes'][f['path']]
 assert count==m['source_changed_lines'] and count<50
 m['verification']=[{'check':'git diff --no-index --numstat','source_changed_lines':count,'numstat':numstat},{'check':'source SHA256 unchanged','passed':True}]
 path=lambda x:str(x).removeprefix('\\\\?\\')
 args=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','3g','--cpus','2','--pids-limit','128','--tmpfs','/tmp:rw,size=256m','--mount',f'type=bind,source={path(out)},target=/output','--mount',f'type=bind,source={ROOT / "datasets/data_analysis"},target=/input,readonly','local-llm-benchmark:1.0']
 if e['task']=='data_analysis':args+=['python','/output/analysis.py']
 else:args+=['sh','-c','ln -s /opt/lab/node_modules /output/game/node_modules; node /opt/lab/browser_probe.mjs']
 r=subprocess.run(args,capture_output=True,text=True,timeout=180)
 (d/'validation.log').write_text(r.stdout+'\n'+r.stderr)
 if e['task']=='racing_game':
  v=json.loads((out/'browser_validation.json').read_text()) if (out/'browser_validation.json').exists() else {}
  runnable=bool(v.get('build') and v.get('loads') and not v.get('errors'))
 else:
  runnable=r.returncode==0 and 'Error reading' not in r.stdout
  if 'nano' in e['model']:
   runnable=runnable and all(json.loads(f.read_text()) for f in out.glob('profiling_*.json'))
 m.update(status='validated_partial' if runnable else 'validation_failed',runnable=runnable,completion=False,artifacts_path=path(out),source_artifacts_path=path(source))
 m['verification'].append({'check':'Docker network none isolated execution','exit_code':r.returncode,'runnable':runnable,'log':'validation.log'})
 p.write_text(json.dumps(m,indent=2)); print(e['model'],count,m['status'],flush=True)
