import {chromium} from '/opt/lab/node_modules/playwright/index.mjs';
import {spawn} from 'node:child_process';
import fs from 'node:fs';
const model=process.argv[2];
const server=spawn('/opt/lab/node_modules/.bin/vite',['--host','127.0.0.1','--port','4174','--strictPort','--configLoader','native'],{cwd:'/output/game'});
let browser;
const result={model,errors:[],instrumentation:'Validation-only response instrumentation exposes existing local state; candidate source is unchanged.'};
try {
 await new Promise(r=>setTimeout(r,2000));
 browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1280,height:720}});
 page.on('pageerror',e=>result.errors.push(String(e)));
 await page.route('**/src/main.js',async route=>{
  const response=await route.fetch();let body=await response.text();
  const expression=model==='nemotron3'?'({position:car.position.toArray(),direction:carDirection,speed:carSpeed})':model==='qwen9'?'({position:gameState.playerCar.position.toArray(),direction:gameState.playerCar.mesh.rotation.y,speed:gameState.playerCar.velocity.length()})':'({position:car.getCar().position.toArray(),direction:car.getCar().rotation.y,speed:car.getVelocity().length()})';
  await route.fulfill({response,body:body+'\nwindow.__REPAIR_CHECK__=()=>'+expression+';'});
 });
 await page.goto('http://127.0.0.1:4174');await page.waitForTimeout(300);
 result.viewport=await page.evaluate(()=>{const r=document.querySelector('canvas').getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:document.documentElement.scrollHeight};});
 result.canvas_fits=result.viewport.left===0&&result.viewport.top===0&&result.viewport.right<=result.viewport.width&&result.viewport.bottom<=result.viewport.height&&result.viewport.scrollWidth===result.viewport.width&&result.viewport.scrollHeight===result.viewport.height;
 const read=()=>page.evaluate(()=>window.__REPAIR_CHECK__());
 result.before=await read();await page.keyboard.down('w');await page.waitForTimeout(700);result.accelerated=await read();
 await page.keyboard.down('a');await page.waitForTimeout(700);await page.keyboard.up('a');await page.keyboard.up('w');result.steered=await read();
 result.movement=result.accelerated.position.some((x,i)=>Math.abs(x-result.before.position[i])>0.01);
 result.steering=Math.abs(result.steered.direction-result.accelerated.direction)>0.01;
 await page.screenshot({path:'/output/screenshots/keyboard_verified.png'});
}catch(e){result.errors.push(String(e));}finally{
 if(browser)await browser.close();server.kill('SIGTERM');fs.writeFileSync('/output/keyboard_validation.json',JSON.stringify(result,null,2));
}
