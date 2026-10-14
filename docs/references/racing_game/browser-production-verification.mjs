import {chromium} from '../../../../sandbox/node_modules/playwright/index.mjs';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const evidence={kind:'Actual Chromium production route smoke test; keyboard input and read-only diagnostics',url:'http://127.0.0.1:8765/api/references/racing_game/files/output/game/dist/index.html',startedAt:new Date().toISOString(),errors:[],requestFailures:[],checks:[],screenshots:[]};
const browser=await chromium.launch({headless:true,args:['--enable-webgl']});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
page.on('pageerror',e=>evidence.errors.push(e.message));
page.on('requestfailed',r=>evidence.requestFailures.push({url:r.url(),failure:r.failure()}));
const snapshot=()=>page.evaluate(()=>window.solstice.snapshot());
const record=name=>{evidence.checks.push({name,passed:true});console.log('PASS',name);};
async function capture(name){const path=fileURLToPath(new URL(`./output/screenshots/production_${name}.png`,import.meta.url));await page.screenshot({path});evidence.screenshots.push(path);}
try{
 const response=await page.goto(evidence.url);evidence.httpStatus=response.status();evidence.headers=await response.allHeaders();assert.equal(response.status(),200);await page.waitForFunction(()=>window.solstice);await page.waitForTimeout(500);assert.ok((await snapshot()).inMenu);await capture('menu');record('Production route loads WebGL scene under dashboard response headers');
 await page.click('[data-car="1"]');assert.equal((await snapshot()).cars[0].car,'spectre');await page.click('#start');await page.waitForFunction(()=>solstice.snapshot().phase==='racing',null,{timeout:45000});record('Selected Spectre R starts after countdown');
 const before=await snapshot();await page.keyboard.down('w');await page.waitForTimeout(1800);await page.keyboard.up('w');const after=await snapshot();assert.ok(after.cars[0].speed>3);assert.ok(Math.hypot(after.cars[0].x-before.cars[0].x,after.cars[0].z-before.cars[0].z)>1);record('W accelerates and moves player in production build');
 await page.keyboard.press('p');assert.ok((await snapshot()).paused);const frozen=(await snapshot()).time;await page.waitForTimeout(200);assert.equal((await snapshot()).time,frozen);record('Pause freezes production race');
 for(const view of ['chase','hood','overhead']){assert.equal((await snapshot()).camera,view.toUpperCase());await capture(`race_${view}`);await page.keyboard.press('c');await page.waitForTimeout(200);}record('All three production camera views render');
 await page.keyboard.press('Escape');assert.equal((await snapshot()).paused,false);await page.keyboard.press('r');assert.equal((await snapshot()).phase,'countdown');record('Escape resumes and R restarts production game');
 evidence.snapshot=await snapshot();assert.equal(evidence.errors.length,0);assert.equal(evidence.requestFailures.length,0);record('No uncaught JavaScript errors or failed network requests');evidence.passed=true;
}catch(e){evidence.passed=false;evidence.failure={message:e.message,stack:e.stack};process.exitCode=1;console.error(e);}
finally{evidence.completedAt=new Date().toISOString();fs.writeFileSync(new URL('./production-browser-verification.json',import.meta.url),JSON.stringify(evidence,null,2));await browser.close();}
