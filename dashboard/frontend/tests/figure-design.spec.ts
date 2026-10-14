import {test,expect} from '@playwright/test';
import {modelLabel} from '../src/modelNames';
import {buildFigureCharts,figureLabels,detectiveCaseAverages} from '../src/figureCharts';
import {modelStyles} from '../src/chartStyles';
import type {Run} from '../src/types';

test('short labels identify the roster without changing package identities',async({request})=>{
 const summary=await (await request.get('/api/summary')).json();
 const names=summary.models.map((m:{name:string})=>m.name),labels=names.map(modelLabel);
 expect(new Set(labels).size).toBe(names.length);
 expect(modelLabel('qwen3.5:9b-q4_K_M')).toBe('Qwen 3.5 · 9B');
 expect(modelLabel('qwen3.5:27b-q4_K_M')).toBe('Qwen 3.5 · 27B');
 expect(modelLabel('qwen3.5:9b-q8_0')).toBe('qwen3.5:9b-q8_0');
 expect(labels.every((name:string)=>!name.includes('q4_K_M'))).toBeTruthy();
});

test('scoped labels omit repeated context and keep duplicate attempts distinct',async({request})=>{
 const summary=await (await request.get('/api/summary')).json();
 const base=summary.runs.find((r:Run)=>r.task==='racing_game') as Run;
 const rows=[{...base,status:'evaluated',run_id:'first',start:'2026-10-01T00:00:00Z'},{...base,status:'evaluated',run_id:'second',start:'2026-10-02T00:00:00Z'}];
 const taskLabels=figureLabels(rows,'task');
 expect(taskLabels[0]).toBe(`${modelLabel(base.model.name)} · Attempt 1`);
 expect(taskLabels[1]).toBe(`${modelLabel(base.model.name)} · Attempt 2`);
 expect(figureLabels([...rows].reverse(),'task')).toEqual([...taskLabels].reverse());
 expect(figureLabels(rows,'model')).toEqual(['Racing game · Attempt 1','Racing game · Attempt 2']);
 const tracks=[{...rows[0],task:'detective',case:'case_a',sensory_track:'multimodal'},{...rows[1],task:'detective',case:'case_a',sensory_track:'text_only_detective'}];
 expect(figureLabels(tracks,'task')[0]).toContain('Visual');
 expect(figureLabels(tracks,'task')[1]).toContain('Text only');
 expect(figureLabels([{...rows[0],status:'failed'}],'task')[0]).toContain('Failed');
 const figures=buildFigureCharts(rows,'task',modelStyles(summary.models));
 expect(figures).toHaveLength(11);
 expect(figures.filter(f=>f.group==='Performance')).toHaveLength(4);
 const pending=rows.map(r=>({...r,after_updates:{status:'running',scored:false,initial_seconds:0,extra_seconds:0}}));
 const pendingFigures=buildFigureCharts(pending,'task',modelStyles(summary.models));
 for(const title of ['Verified points','Automatic checks passed','Speed and verified points'])expect(pendingFigures.find(f=>f.title===title)?.emptyMessage).toBeTruthy();
});

test('Detective figures average cases equally, preserve missing values and separate protocols and tracks',async({request})=>{
 const summary=await (await request.get('/api/summary')).json();
 const base=summary.runs.find((r:Run)=>r.task==='detective'&&r.sensory_track!=='text_only_detective') as Run;
 const sample=(id:string,caseId:string,speed:number|null,time:number,points:number,complete=false):Run=>({...base,run_id:id,case:caseId,status:'evaluated',protocol_hash:'same-protocol',repetition:1,task_seconds:time,scores:{...base.scores,verified_points:points,complete},performance:{...base.performance,generation_tps:speed,peak_vram_bytes:null}});
 const rows=[sample('a','case_01',10,60,30,true),sample('b','case_02',20,120,60),sample('c','case_03',null,180,90),sample('retry','case_01',30,60,30,true)];
 const frozen=JSON.stringify(rows),figures=buildFigureCharts(rows,'task',modelStyles(summary.models));
 for(const chart of figures.filter(f=>f.bars))expect(chart.bars).toHaveLength(1);
 const bar=(title:string)=>figures.find(f=>f.title===title)!.bars![0];
 // Within-case means first; the extra case_01 attempt cannot increase its weight.
 expect(bar('Generation speed').value).toBe(20);
 expect(bar('Time taken').value).toBe(2);
 expect(bar('Verified points').value).toBe(60);
 expect(bar('Automatic checks passed').value).toBeCloseTo(100/3);
 expect(bar('Peak VRAM').value).toBeNull();
 expect(bar('Generation speed').detail).toContain('2/3 cases with recorded values');
 expect(bar('Time taken').label).toContain('Average · 3 cases');
 const scatter=figures.find(f=>f.title==='Speed and verified points')!.option.series as {data:{value:number[]}[]}[];
 expect(scatter[0].data).toHaveLength(1);expect(scatter[0].data[0].value).toEqual([20,45]);
 expect(JSON.stringify(rows)).toBe(frozen);
 const separated=detectiveCaseAverages([...rows,{...rows[0],run_id:'text',sensory_track:'text_only_detective'},{...rows[0],run_id:'old',protocol_hash:'old-protocol'},{...rows[0],run_id:'rep2',repetition:2}]);
 expect(separated).toHaveLength(4);
 const pending=rows.map(r=>({...r,after_updates:{status:'running',scored:false,initial_seconds:0,extra_seconds:0}}));
 const pendingFigures=buildFigureCharts(pending,'task',modelStyles(summary.models));
 expect(pendingFigures.find(f=>f.title==='Verified points')!.bars![0].value).toBeNull();
 expect(pendingFigures.find(f=>f.title==='Automatic checks passed')!.bars![0].value).toBeNull();
 expect(pendingFigures.find(f=>f.title==='Speed and verified points')!.emptyMessage).toBeTruthy();
});

test('figures lead the comparison and retain readable type on desktop and mobile',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('/');
 const figures=page.getByRole('region',{name:'Figure selection',exact:true});
 await expect(figures.getByRole('button',{name:'One task',exact:true})).toHaveAttribute('aria-pressed','true');
 await expect(figures.getByRole('combobox',{name:'Task for figures',exact:true})).toHaveValue('racing_game');
 await expect(page.locator('.figure-group .chart [role=img]')).toHaveCount(11);
 const chartTop=await page.locator('.figure-group').first().evaluate(el=>el.getBoundingClientRect().top);
 const tableTop=await page.locator('.attempt-section').evaluate(el=>el.getBoundingClientRect().top);
 expect(chartTop).toBeLessThan(tableTop);
 expect(await page.locator('body').evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBe(18);
 expect(await page.locator('.chart h3').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(19);
 await page.locator('.figure-group .section-heading').first().scrollIntoViewIfNeeded();
 await page.screenshot({path:'../../results/reports/dashboard-redesign-desktop.png'});
 await page.locator('.figure-group .chart').first().screenshot({path:'../../results/reports/dashboard-redesign-chart.png'});
 await figures.getByRole('button',{name:'One model',exact:true}).click();
 const models=figures.getByRole('combobox',{name:'Model for figures',exact:true});
 await models.selectOption('qwen3.5:9b-q4_K_M');
 await expect(models.locator('option:checked')).toHaveText('Qwen 3.5 · 9B');
 await expect(page.locator('.figure-context h3')).toHaveText('Qwen 3.5 · 9B');
 await figures.getByRole('button',{name:'All results',exact:true}).click();
 await expect(page.locator('.figure-group .chart [role=img]')).toHaveCount(11);
 await figures.getByRole('button',{name:'One task',exact:true}).click();
 for(const width of [768,390,320]){
  await page.setViewportSize({width,height:900});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  expect(await figures.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBeTruthy();
  const sizes=await page.locator('.chart h3,.chart-subtitle,.figure-context p').evaluateAll(elements=>elements.map(el=>parseFloat(getComputedStyle(el).fontSize)));
  expect(sizes.every(size=>size>=18)).toBeTruthy();
  if(width===390){
   await expect(page.locator('.compact-bars').first()).toBeVisible();
   expect(await page.locator('.compact-bar-track').first().evaluate(el=>el.getBoundingClientRect().width)).toBeGreaterThan(240);
   await page.locator('.figure-group .section-heading').first().scrollIntoViewIfNeeded();
   await page.screenshot({path:'../../results/reports/dashboard-redesign-mobile.png'});
  }
 }
 await page.reload();await expect(figures.getByRole('combobox',{name:'Task for figures',exact:true})).toHaveValue('racing_game');
 await page.setViewportSize({width:1440,height:1000});
 await expect(page.locator('.compact-bars')).toHaveCount(0);
 await expect(page.locator('.figure-group .chart canvas').first()).toBeVisible();
 expect(errors).toEqual([]);
});
