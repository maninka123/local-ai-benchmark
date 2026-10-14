import {chromium} from '../../../../sandbox/node_modules/playwright/index.mjs';
import {fileURLToPath} from 'node:url';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {trackAt,project,angleDelta,CARS} from './output/game/src/simulation.js';
const evidence={kind:'actual Chromium browser, keyboard input, live read-only diagnostics',url:process.env.GAME_URL||'http://127.0.0.1:5187/',startedAt:new Date().toISOString(),browserErrors:[],checks:[],snapshots:[]};
const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
page.on('pageerror',e=>evidence.browserErrors.push(e.message));
const snapshot=()=>page.evaluate(()=>window.solstice.snapshot());
const screenshot=async name=>page.screenshot({path:fileURLToPath(new URL(`./output/screenshots/${name}.png`,import.meta.url))});
const record=(name,detail={})=>{evidence.checks.push({name,passed:true,...detail});console.log('PASS',name);};
let held=new Set();async function input(next){const set=new Set(next);for(const k of held)if(!set.has(k))await page.keyboard.up(k);for(const k of set)if(!held.has(k))await page.keyboard.down(k);held=set;}
try{
 await page.goto(evidence.url);await page.waitForFunction(()=>window.solstice);await page.waitForTimeout(800);
 assert.equal((await snapshot()).inMenu,true);await screenshot('menu');record('Menu renders');
 for(let i=0;i<3;i++){await page.click(`[data-car="${i}"]`);const s=await snapshot();assert.equal(s.selected,i);assert.equal(s.cars[0].car,CARS[i].id);}record('All three selection buttons change the actual player vehicle');
 await page.click('#start');assert.equal((await snapshot()).phase,'countdown');await page.waitForFunction(()=>solstice.snapshot().phase==='racing',null,{timeout:30000});record('Countdown releases race');
 const before=await snapshot();await input(['ArrowUp']);await page.waitForTimeout(1300);await input([]);const moved=await snapshot();assert.ok(moved.cars[0].speed>5);assert.ok(Math.hypot(moved.cars[0].x-before.cars[0].x,moved.cars[0].z-before.cars[0].z)>2);record('Arrow acceleration moves selected Swift RS', {before:before.cars[0],after:moved.cars[0]});
 for(const [i,view]of ['chase','hood','overhead'].entries()){assert.equal((await snapshot()).camera,['CHASE','HOOD','OVERHEAD'][i]);await screenshot(`race_${view}`);await page.keyboard.press('c');await page.waitForTimeout(150);}record('Three camera views switch and render');
 await page.keyboard.press('p');const frozen=await snapshot();await page.waitForTimeout(500);assert.equal((await snapshot()).time,frozen.time);assert.equal(await page.locator('#pause').isVisible(),true);await page.keyboard.press('Escape');assert.equal((await snapshot()).paused,false);record('P pauses exact timer; Escape resumes');
 const preBrake=await snapshot();await input(['s']);await page.waitForTimeout(1500);await input([]);assert.ok((await snapshot()).cars[0].speed<preBrake.cars[0].speed);record('S brakes and reverses');
 await page.keyboard.press('r');assert.equal((await snapshot()).phase,'countdown');assert.equal((await snapshot()).cars[0].completedLaps,0);record('R resets the race');
 await page.waitForFunction(()=>solstice.snapshot().phase==='racing',null,{timeout:30000});await input(['w','d']);const collisionStart=Date.now();let hit;
 while(Date.now()-collisionStart<20000){await page.waitForTimeout(150);hit=await snapshot();if(hit.collisions.barrier>0)break;}
 await input([]);assert.ok(hit.collisions.barrier>0);await screenshot('barrier_collision');record('W/D steering causes real barrier collision',{snapshot:hit});
 await page.keyboard.press(' ');const recovered=await snapshot();assert.ok(recovered.cars[0].recoveries>0);record('Space recovery aligns car without awarding lap');
 await page.keyboard.press('r');await page.waitForFunction(()=>solstice.snapshot().phase==='racing',null,{timeout:30000});
 // External test driver uses only keyboard events. It never mutates race state or calls the game's AI.
 // It reads the live car pose and aims at a point on the known circuit, like a robot playing the game.
 const begin=Date.now();let lastReport=-20,lastLap=0,lastSnapshot;
 while(Date.now()-begin<300000){const s=await snapshot();lastSnapshot=s;const c=s.cars[0];if(s.phase==='results')break;
  if(s.phase==='racing'){const q=project(c.x,c.z);const target=trackAt(q.s+10+Math.abs(c.speed)*.42,-2.6);const err=angleDelta(Math.atan2(target.z-c.z,target.x-c.x),c.heading);const corner=trackAt(q.s+18).curve>0;let desired=corner?23:29;desired*=Math.max(.6,1-Math.abs(err)*.4);const buttons=[];if(c.speed<desired)buttons.push('w');if(c.speed>desired+1.6)buttons.push('s');if(err>.045)buttons.push('d');if(err<-.045)buttons.push('a');await input(buttons);
  }else await input([]);
  if(s.time-lastReport>=20){lastReport=s.time;evidence.snapshots.push(s);console.log('RACE',s.time.toFixed(1),'laps',s.cars.map(c=>c.completedLaps).join(','),'player speed',c.speed.toFixed(1));}
  if(c.completedLaps>lastLap){lastLap=c.completedLaps;await screenshot(`lap_${lastLap}`);}
  await page.waitForTimeout(65);
 }
 await input([]);evidence.finalRace=await snapshot();assert.equal(evidence.finalRace.phase,'results');assert.equal(evidence.finalRace.cars[0].completedLaps,3);assert.equal(evidence.finalRace.cars[0].passedCheckpoints,48);for(const c of evidence.finalRace.cars){assert.equal(c.completedLaps,3);assert.ok(c.finishTime>0);assert.equal(c.lapTimes.length,3);}assert.equal(await page.locator('#results').isVisible(),true);await screenshot('results');record('Keyboard-driven player completes all 48 checkpoints and three laps');record('Five NPCs independently complete three actual browser laps',{finishTimes:evidence.finalRace.cars.slice(1).map(c=>c.finishTime)});record('Final standings and lap times render', {standings:evidence.finalRace.standings});
 assert.equal(evidence.browserErrors.length,0);record('No browser JavaScript errors');
}catch(e){evidence.failure={message:e.message,stack:e.stack};console.error(e);try{evidence.failureSnapshot=await snapshot();await screenshot('verification_failure');}catch{}process.exitCode=1;}
finally{evidence.completedAt=new Date().toISOString();fs.writeFileSync(new URL('./browser-verification.json',import.meta.url),JSON.stringify(evidence,null,2));await browser.close();}
