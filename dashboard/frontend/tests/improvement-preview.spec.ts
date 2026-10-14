import {test,expect} from '@playwright/test';

test('stage chooser preserves first improvement and the report exposes separate scores',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Task progress',exact:true}).click();
 const chooser=page.getByRole('combobox',{name:'Improvement stage'});
 await chooser.selectOption('1');await expect(page.getByRole('heading',{name:'Task progress · improvement 1'})).toBeVisible();
 await expect(page.locator('.board-status').filter({hasText:'Failed to complete on attempt 2'})).toHaveCount(53);
 await chooser.selectOption('2');await expect(page.getByRole('heading',{name:'Task progress · improvement 2'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Open results report'})).toHaveAttribute('href','/api/benchmark-report');
 await page.screenshot({path:'../../results/reports/dashboard-improvement-2.png',fullPage:true});
 await page.goto('/api/benchmark-report');await expect(page.locator('table')).toHaveCount(2);
 await expect(page.getByRole('columnheader',{name:'Initial points',exact:true})).toBeVisible();
 await expect(page.getByRole('columnheader',{name:'Improvement 2 points',exact:true})).toBeVisible();
 await expect(page.getByText('5.7 verified / 45.0 pending',{exact:true}).first()).toBeVisible();
 await page.screenshot({path:'../../results/reports/improvement-results-report.png'});
 await page.setViewportSize({width:390,height:844});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
});

test('a saved racing build opens in the dashboard and closes its local container',async({page})=>{
 test.setTimeout(70000);
 const summary=await (await page.request.get('/api/summary')).json();
 const runs=summary.runs.filter((r:any)=>summary.campaign.run_ids.includes(r.run_id)&&r.task==='racing_game'&&r.scores.evidence.build_success);
 const run=runs.find((r:any)=>r.model.name==='qwen3.5:27b-q4_K_M')??runs[0];expect(run).toBeTruthy();
 await page.goto(`/?run_id=${encodeURIComponent(run.run_id)}`);
 await page.getByRole('button',{name:'Initial results',exact:true}).click();
 const panel=page.getByRole('region',{name:'Initial racing game',exact:true});
 await panel.getByRole('button',{name:'Open game preview'}).click();
 const dialog=page.getByRole('dialog',{name:/Initial racing game/});const frame=dialog.locator('iframe');await expect(frame).toBeVisible({timeout:45000});
 await expect(frame).toHaveAttribute('sandbox','allow-scripts allow-pointer-lock');
 await expect.poll(()=>page.frames().some(f=>f.url().startsWith('http://127.0.0.1:')&&!f.url().includes(':8765/'))).toBeTruthy();
 await dialog.screenshot({path:'../../results/reports/dashboard-game-preview.png'});
 await dialog.getByRole('button',{name:'Close preview'}).click();await expect(frame).toHaveCount(0);
 await expect(panel.getByRole('button',{name:'Open game preview'})).toBeEnabled();
});

test('preview startup failure explains the error and permits retry',async({page})=>{
 const summary=await (await page.request.get('/api/summary')).json();
 const run=summary.runs.find((r:any)=>summary.campaign.run_ids.includes(r.run_id)&&r.task==='racing_game'&&r.scores.evidence.build_success);expect(run).toBeTruthy();
 let attempts=0;
 await page.route('**/api/run/*/game*',route=>{
  if(route.request().method()==='DELETE')return route.fulfill({json:{stopped:true}});
  attempts++;return route.fulfill({status:503,json:{detail:'Game preview service is unavailable. Check Docker and try again.'}});
 });
 await page.goto(`/?run_id=${encodeURIComponent(run.run_id)}`);await page.getByRole('button',{name:'Initial results',exact:true}).click();
 const panel=page.getByRole('region',{name:'Initial racing game',exact:true});const open=panel.getByRole('button',{name:'Open game preview'});
 await open.click();const dialog=page.getByRole('dialog',{name:/Initial racing game/});await expect(dialog.getByRole('alert')).toContainText('Check Docker');
 await dialog.getByRole('button',{name:'Try again'}).click();await expect.poll(()=>attempts).toBe(2);await dialog.getByRole('button',{name:'Close preview'}).click();await expect(open).toBeEnabled();
 await page.getByRole('combobox',{name:'Task',exact:true}).selectOption('data_analysis');await expect(page.locator('.game-preview')).toHaveCount(0);
});
