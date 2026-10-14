import _bootstrap,uuid,shutil
from benchmark.util import ROOT,write_json,now
from benchmark.harness.execution_manager import Sandbox
from benchmark.common_tools.browser_tools import browser_probe

run=ROOT/'logs'/('game-environment-'+uuid.uuid4().hex[:8]);(run/'input').mkdir(parents=True);(run/'artifacts').mkdir()
shutil.copytree(ROOT/'datasets'/'racing_game'/'game',run/'input'/'game')
with Sandbox(run) as box:
    box.exec(['bash','-lc','cp -r /input/game /output/game && ln -s /opt/lab/node_modules /output/game/node_modules'])
    source="""import * as THREE from 'three';
const scene=new THREE.Scene();scene.background=new THREE.Color('#314159');const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,.1,100);camera.position.z=5;
const renderer=new THREE.WebGLRenderer();renderer.setSize(innerWidth,innerHeight);document.body.appendChild(renderer.domElement);
scene.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial({color:'#62dbc5'})));renderer.render(scene,camera);
document.body.insertAdjacentHTML('beforeend','<p>Three.js environment smoke</p>');
"""
    from benchmark.harness.execution_manager import filesystem
    filesystem(box,'write','/output/game/src/main.js',source)
    browser_probe(box)
result=__import__('json').loads((run/'artifacts'/'browser_validation.json').read_text(encoding='utf-8'))
good=result['build'] and result['loads'] and result['checks'].get('canvas') and not result['errors']
write_json(ROOT/'results'/'game_environment_validation.json',{'passed':good,'timestamp':now(),'path':str(run.relative_to(ROOT)),'browser':result})
if not good:raise RuntimeError(result)
print('Sandboxed Three.js/Vite build and Chromium render passed.')
