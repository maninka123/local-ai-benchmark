import json, hashlib, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'results/improvement_campaign/pass_2/campaign.json').read_text())
summaries={
 'qwen3.5:9b-q4_K_M':'Convert CatmullRom control points to Vector3, use the closed-curve boolean, and render the existing static scene while in menu state. Static preview only; driving remains unavailable.',
 'glm-4.7-flash:q4_K_M':'Restrict product/customer joins to required columns and preserve distinct regional names so existing six-plot/findings generation runs.',
 'nemotron-3-nano:30b-a3b-q4_K_M':'Serialize pandas dtype objects as strings so existing six-table profiling writes valid JSON.',
 'nemotron3:33b-q4_K_M':'Repair WASD codes, connect steering to vehicle rotation, scale movement/friction by elapsed time, and prevent orbit updates overriding the existing chase camera.',
 'gpt-oss:20b':'Use actual regional name and inventory month fields, and correct existing segment-leader and stockout-peak finding labels.',
 'qwen3-vl:30b-a3b-instruct':'Repair Car/OrbitControls imports, retain vector positions, initialize acceleration/velocity, return NPC meshes, and connect existing steering to directional movement.'}
for e in c['entries']:
 if len(sys.argv)>1 and e['model'] not in sys.argv[1:]:continue
 d=Path('\\\\?\\'+str(Path(e['further_folder']).parent/'repairs/sol-6.1-small-fix-20261014'));p=d/'repair.json'
 if not p.exists():continue
 m=json.loads(p.read_text());out=d/'artifacts';source=Path(m['source_artifacts_path']);count=0
 for f in m['source_files']:
  r=subprocess.run(['git','-c','core.longpaths=true','diff','--no-index','--numstat','--',str(source/f['path']).removeprefix('\\\\?\\'),str(out/f['path']).removeprefix('\\\\?\\')],capture_output=True,text=True)
  assert r.returncode in(0,1)
  count+=sum(sum(map(int,row.split('\t')[:2])) for row in r.stdout.splitlines())
  assert hashlib.sha256((source/f['path']).read_bytes()).hexdigest()==m['source_hashes'][f['path']]
 assert count==m['source_changed_lines'] and count<50
 m['changes_summary']=summaries[e['model']]+(' Remove default page margins and fit the canvas to the iframe viewport.' if e['task']=='racing_game' else '')
 k=out/'keyboard_validation.json'
 if k.exists():
  v=json.loads(k.read_text());m['verification'].append({'check':'Isolated real WASD movement and steering','passed':v['movement'] and v['steering'] and not v['errors'],'evidence':'artifacts/keyboard_validation.json','validation_only_instrumentation':True})
  m['keyboard_movement_verified']=v['movement'];m['keyboard_steering_verified']=v['steering']
  if 'canvas_fits' in v:m['verification'].append({'check':'Canvas fits browser viewport without page overflow','passed':v['canvas_fits'],'evidence':'artifacts/keyboard_validation.json'});assert v['canvas_fits']
 if e['task']=='data_analysis' and 'nano' not in e['model']:
  files=list((out/'figures').glob('figure_*.png'));assert len(files)>=6
  assert all(f.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for f in files)
  json.loads((out/'findings.json').read_text())
  m['verification'].append({'check':'Six regenerated PNG figures and valid findings JSON','passed':True})
 if e['model']=='qwen3.5:9b-q4_K_M':m['keyboard_movement_verified']=False;m['keyboard_steering_verified']=False
 m['limitations'].append('Original benchmark scores and completeness are unchanged. This is an assisted partial preview, with original report claims retained and potentially inaccurate.')
 m['completion']=False;p.write_text(json.dumps(m,indent=2));print(e['model'],count,m['runnable'])
