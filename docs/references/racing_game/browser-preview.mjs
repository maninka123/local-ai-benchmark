import {chromium} from '../../../../sandbox/node_modules/playwright/index.mjs';
import {fileURLToPath} from 'node:url';
const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=swiftshader','--disable-web-security']});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
page.on('pageerror',e=>console.log('ERROR',e.message));
await page.goto('http://127.0.0.1:5187');await page.waitForFunction(()=>window.solstice);await page.waitForTimeout(1200);
await page.screenshot({path:fileURLToPath(new URL('./output/screenshots/menu.png',import.meta.url))});
console.log(await page.evaluate(()=>({snapshot:solstice.snapshot(),body:document.body.innerText.slice(0,600)})));
await page.click('#start');await page.waitForTimeout(4400);await page.keyboard.down('w');await page.waitForTimeout(1600);await page.keyboard.up('w');
for(const view of ['chase','hood','overhead']){await page.screenshot({path:fileURLToPath(new URL(`./output/screenshots/race_${view}.png`,import.meta.url))});await page.keyboard.press('c');await page.waitForTimeout(350);}
console.log(JSON.stringify(await page.evaluate(()=>solstice.snapshot()),null,2));await browser.close();
