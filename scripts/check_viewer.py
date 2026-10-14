import _bootstrap,subprocess,json,socket,uuid
from benchmark.util import ROOT,read_json,write_json,now

validation=read_json(ROOT/'results'/'game_environment_validation.json');dist=ROOT/validation['path']/'artifacts'/'game'/'dist'
assert validation['passed'] and dist.is_dir()
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
name='llmb-view-smoke-'+uuid.uuid4().hex[:8]
args=['docker','run','-d','--name',name,'--network','bridge','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2','--pids-limit','64','--user','1000:1000','--tmpfs','/tmp:rw,size=64m','-p',f'127.0.0.1:{port}:8000','--mount',f'type=bind,source={dist.resolve()},target=/site,readonly','local-llm-benchmark:1.0','python','/opt/lab/viewer_server.py']
subprocess.run(args,check=True,capture_output=True)
script=ROOT/'logs'/'viewer-smoke.mjs'
script.write_text("""import {chromium} from '../dashboard/frontend/node_modules/playwright-core/index.mjs';
const browser=await chromium.launch();const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto('http://127.0.0.1:8765');await page.setContent('<iframe sandbox="allow-scripts allow-pointer-lock" src="http://127.0.0.1:PORT" style="width:1280px;height:720px"></iframe>');await page.waitForTimeout(4000);const frame=page.frames().find(f=>f.url().includes(':PORT'));console.log(JSON.stringify({canvas:await frame.locator('canvas').count(),text:await frame.locator('body').innerText(),errors}));await browser.close();""".replace('PORT',str(port)),encoding='utf-8')
try:
    result=subprocess.run(['node',str(script)],capture_output=True,text=True,timeout=30)
    if result.returncode:raise RuntimeError(result.stderr)
    value=json.loads(result.stdout.strip());good=value['canvas']==1 and not value['errors'];write_json(ROOT/'results'/'viewer_validation.json',{'passed':good,'timestamp':now(),'result':value})
    if not good:raise RuntimeError(value)
    print('Read-only isolated game viewer renders inside sandboxed dashboard iframe.')
finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
