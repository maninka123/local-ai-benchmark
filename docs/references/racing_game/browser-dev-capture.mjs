import {chromium} from '../../../../sandbox/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const evidence={kind:'Development-server browser smoke test and fresh screenshot capture after interrupted verification',startedAt:new Date().toISOString(),url:'http://127.0.0.1:5187/',errors:[],screenshots:[]};
const browser=await chromium.launch({headless:true,args:['--enable-webgl']});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
page.on('pageerror',e=>evidence.errors.push(e.message));
async function capture(name){const target=new URL(`./output/screenshots/${name}.png`,import.meta.url);if(fs.existsSync(target))fs.copyFileSync(target,new URL(`./output/screenshots/${name}.interrupted.png`,import.meta.url));await page.screenshot({path:fileURLToPath(target)});evidence.screenshots.push(name);}
try {
 await page.goto(evidence.url);await page.waitForFunction(()=>window.solstice);await page.waitForTimeout(5000);
 await capture('menu');
 await page.click('[data-car="2"]');await page.click('#start');await page.waitForFunction(()=>solstice.snapshot().phase==='racing',null,{timeout:60000});
 await page.keyboard.down('w');await page.waitForTimeout(1800);await page.keyboard.up('w');
 for(const view of ['chase','hood','overhead']){await page.waitForTimeout(500);await capture(`race_${view}`);await page.keyboard.press('c');}
 evidence.snapshot=await page.evaluate(()=>solstice.snapshot());evidence.passed=evidence.errors.length===0;
} catch(e){evidence.passed=false;evidence.failure=e.message;process.exitCode=1;}
finally{evidence.completedAt=new Date().toISOString();fs.writeFileSync(new URL('./development-browser-verification.json',import.meta.url),JSON.stringify(evidence,null,2));await browser.close();console.log(JSON.stringify(evidence,null,2));}
