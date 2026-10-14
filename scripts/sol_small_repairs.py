"""Repair coordinator: never imports or executes candidate code on host."""
import json, shutil, hashlib, subprocess, difflib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RID='sol-6.1-small-fix-20261014'
campaign=json.loads((ROOT/'results/improvement_campaign/pass_2/campaign.json').read_text())
targets={('nemotron3:33b-q4_K_M','racing_game'),('gpt-oss:20b','data_analysis'),('glm-4.7-flash:q4_K_M','data_analysis'),('nemotron-3-nano:30b-a3b-q4_K_M','data_analysis'),('qwen3.5:9b-q4_K_M','racing_game'),('qwen3-vl:30b-a3b-instruct','racing_game')}
for e in campaign['entries']:
 if (e['model'],e['task']) not in targets: continue
 if len(sys.argv)>1 and e['model'] not in sys.argv[1:]:continue
 source=Path('\\\\?\\'+str(ROOT/e['evaluation']['snapshot_path']/'artifacts'))
 dest=Path('\\\\?\\'+str(Path(e['further_folder']).parent/'repairs'/RID))
 out=dest/'artifacts'
 shutil.copytree(source,out,dirs_exist_ok=True,ignore=shutil.ignore_patterns('node_modules'))
 changes={}
 def edit(rel,pairs):
  p=out/rel; old=(source/rel).read_text(); new=old
  for a,b in pairs:
   assert a in new,(e['model'],rel,a)
   new=new.replace(a,b)
  p.write_text(new,encoding='utf-8',newline='\n'); changes[rel]=(old,new)
 model=e['model']; task=e['task']
 if model=='nemotron-3-nano:30b-a3b-q4_K_M':
  edit('analysis.py',[('json.dump(summary, f, indent=2)','json.dump(summary, f, indent=2, default=str)')])
 elif model=='gpt-oss:20b':
  edit('analysis.py',[("regions[['region_id','region_name']]","regions[['region_id','name']].rename(columns={'name':'region_name'})"),("pd.to_datetime(inv_stock['date'])","pd.to_datetime(inv_stock['month'])"),("Enterprise segment accounts for {seg_rev['revenue'].iloc[0]","{seg_rev['segment'].iloc[0]} segment accounts for {seg_rev['revenue'].iloc[0]"),("stock_month['month'].iloc[0].strftime('%B %Y')","stock_month.loc[stock_month['stockouts'].idxmax(), 'month'].strftime('%B %Y')"),("{stock_month['stockouts'].iloc[0]} events.","{stock_month['stockouts'].max()} events.")])
 elif model=='glm-4.7-flash:q4_K_M':
  edit('analysis.py',[("transactions.merge(products, on='product_id', how='left')","transactions.merge(products[['product_id', 'name', 'category']], on='product_id', how='left')"),("transactions.merge(customers, on='customer_id', how='left')","transactions.merge(customers[['customer_id', 'segment']], on='customer_id', how='left')"),("transactions.merge(regions, on='region_id', how='left')","transactions.merge(regions.rename(columns={'name':'region_name'}), on='region_id', how='left')"),("product_performance.merge(products, on='product_id')","product_performance.merge(products, on='product_id')"),("transactions.groupby('name')","transactions.groupby('region_name')"),("regional_performance.plot.bar(x='name'","regional_performance.plot.bar(x='region_name'"),("regional_performance.iloc[0]['name']","regional_performance.iloc[0]['region_name']")])
 elif model=='nemotron3:33b-q4_K_M':
  pairs=[("keys['w']","keys['KeyW']"),("keys['s']","keys['KeyS']"),("keys['a']","keys['KeyA']"),("keys['d']","keys['KeyD']"),("function animate() {","const clock = new THREE.Clock();\nfunction animate() {\n  const dt = Math.min(clock.getDelta(), 0.05);"),("carSpeed += acceleration *","carSpeed += acceleration * dt * 60 *"),("carSpeed -= acceleration *","carSpeed -= acceleration * dt * 60 *"),("carDirection -= maxTurnRate *","carDirection += maxTurnRate * dt *"),("carDirection += maxTurnRate * (","carDirection -= maxTurnRate * dt * ("),("  const forward = new THREE.Vector3","  car.rotation.y = carDirection;\n  const forward = new THREE.Vector3"),("addScaledVector(forward, carSpeed)","addScaledVector(forward, carSpeed * dt * 60)"),("carSpeed *= 1 - friction;","carSpeed *= Math.pow(1 - friction, dt * 60);"),("  controls.update();","  // Chase camera is controlled above; OrbitControls would override its orientation.")]
  edit('game/src/main.js',pairs)
 elif model=='qwen3-vl:30b-a3b-instruct':
  edit('game/src/main.js',[("import * as THREE from 'three';","import * as THREE from 'three';\nimport { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';"),('new THREE.OrbitControls(','new OrbitControls(')])
  edit('game/src/Car.js',[('this.position.add(this.velocity.clone().multiplyScalar(deltaTime));','this.position.add(new THREE.Vector3(0, 0, -this.velocity.x).applyQuaternion(this.car.quaternion).multiplyScalar(deltaTime));'),('this.car.rotation.y = Math.atan2(this.velocity.x, this.velocity.z);','this.car.rotation.y -= this.acceleration * this.handling * deltaTime * Math.min(Math.abs(this.velocity.x), 1);'),('this.position = 0;','this.position.set(0, 0, 0);'),('this.acceleration = this.type.accelerationRate;','this.acceleration = this.type.accelerationRate;\n    this.accelerationRate = this.type.accelerationRate;')])
  edit('game/src/NPC.js',[("import * as THREE from 'three';","import * as THREE from 'three';\nimport { Car } from './Car.js';"),('this.position = 0;','this.position.set(0, 0, 0);'),('    this.speed = 0;','    this.speed = 0;\n    this.velocity = new THREE.Vector3();'),('this.car.setCarPosition(this.position);','this.car.setPosition(this.position);'),('return this.car;','return this.car.getCar();')])
 elif model=='qwen3.5:9b-q4_K_M':
  p=source/'game/src/track.js'; old=p.read_text(); pairs=[]
  import re
  for m in re.finditer(r'\{ x: (-?\d+), y: (-?\d+), z: (-?\d+) \}',old): pairs.append((m.group(),f'new THREE.Vector3({m[1]}, {m[2]}, {m[3]})'))
  pairs.append(('    {\n      closed: true,\n      closedLoopPoints: 64\n    }','    true'))
  edit('game/src/track.js',pairs)
  edit('game/src/main.js',[('function animate() {','function animate() {\n  renderer.render(scene, camera);')])
 if task=='racing_game':
  edit('game/index.html',[('</head>','<style>html,body{margin:0;overflow:hidden}canvas{display:block}</style></head>')])
 patches=[]; total=0; files=[]; hashes={}
 for rel,(old,new) in changes.items():
  if old==new: continue
  diff=list(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
  added=sum(x.startswith('+') and not x.startswith('+++') for x in diff); removed=sum(x.startswith('-') and not x.startswith('---') for x in diff)
  total+=added+removed; patches.extend(diff); files.append({'path':rel,'added':added,'removed':removed}); hashes[rel]=hashlib.sha256((source/rel).read_bytes()).hexdigest()
 assert total<50,(model,total)
 (dest/'repair.patch').write_text(''.join(patches))
 manifest={'repair_id':RID,'run_id':e['run_id'],'source_update_id':e['update_id'],'source_evaluation_id':e['evaluation_id'],'configured_model':'gpt-6.1-sol','source_changed_lines':total,'source_files':files,'source_hashes':hashes,'changes_summary':'Bounded runtime/schema repair of existing partial output; no completion claim.','status':'awaiting_isolated_validation','runnable':False,'completion':False,'limitations':e['final_review']['remaining_issues'],'verification':[],'artifacts_path':str(out),'source_artifacts_path':str(source),'model':model,'task':task,'generated_outputs_disclosure':'Existing analysis script may regenerate figures/findings/profiles; report prose is unchanged.'}
 (dest/'repair.json').write_text(json.dumps(manifest,indent=2))
 print(model,task,total,str(dest))


