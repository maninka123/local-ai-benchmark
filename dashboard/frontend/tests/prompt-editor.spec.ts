import {test,expect,Page} from '@playwright/test';

async function editor(page:Page,{paused=false,working=false,large=false}={}){
 const summary=await (await page.request.get('/api/summary')).json();
 const run=summary.runs.find((r:any)=>r.model.name==='qwen3.5:9b-q4_K_M'&&r.task==='racing_game'&&summary.campaign.run_ids.includes(r.run_id));
 const revision:any={revision_id:'rev-aabbccddeeff',base_run_id:run.run_id,model:run.model,task:run.task,status:working?'running':'finished',generation_seconds:0,created:'2026-10-13T00:00:00Z',original_seconds:run.task_seconds,original_scores:run.scores,evaluations:[],prompts:[],workspace_mode:true};
 const workspace:any={run_id:run.run_id,initial_folder:'C:/saved/initial',further_folder:'C:/saved/further',further_exists:true,revision,extra_seconds:0,extra_input_tokens:0,extra_output_tokens:0,processing_paused:paused};
 let cursor=0;
 await page.route('**/api/workspaces/*',route=>{const id=decodeURIComponent(new URL(route.request().url()).pathname.split('/').at(-1)!);return route.fulfill({json:{...workspace,run_id:id}});});
 await page.route('**/api/modifications/rev-aabbccddeeff?*',route=>{const count=large?300:1;const events=Array.from({length:count},(_,i)=>({kind:i%2?'thinking':'output',text:large?'Recent activity '.repeat(80):'Saved activity\n',timestamp:new Date(Date.UTC(2026,9,13,0,0,cursor+i)).toISOString()}));cursor+=count;return route.fulfill({json:{revision,files:[],events,next_cursor:cursor,tools:[],active_seconds:working?10:0}});});
 await page.goto('/');await page.getByRole('button',{name:'Model outputs',exact:true}).click();
 await page.getByRole('combobox',{name:'Model',exact:true}).selectOption('qwen3.5:9b-q4_K_M');
 await page.getByRole('combobox',{name:'Task',exact:true}).selectOption('racing_game');
 await page.getByRole('button',{name:'Further work',exact:true}).click();
 await expect(page.locator('.terminal-directory code')).toHaveText(workspace.further_folder);
 return {workspace,revision,run};
}

test('paused editor accepts typing and retains a separate draft across navigation',async({page})=>{
 await editor(page,{paused:true});const input=page.getByRole('textbox',{name:'Your update prompt',exact:true});
 await input.pressSequentially('Make the steering smooth.\nKeep the car selection.');
 await expect(input).toHaveValue('Make the steering smooth.\nKeep the car selection.');
 await expect(page.getByRole('button',{name:'Processing paused',exact:true})).toBeDisabled();
 await expect(page.getByText('Draft saved in this browser',{exact:true})).toBeVisible();
 await page.getByRole('combobox',{name:'Task',exact:true}).selectOption('data_analysis');await expect(input).toHaveValue('');
 await page.getByRole('combobox',{name:'Task',exact:true}).selectOption('racing_game');await expect(input).toHaveValue('Make the steering smooth.\nKeep the car selection.');
 await page.getByRole('button',{name:'Comparison',exact:true}).click();await page.getByRole('button',{name:'Model outputs',exact:true}).click();
 await page.getByRole('combobox',{name:'Model',exact:true}).selectOption('qwen3.5:9b-q4_K_M');await page.getByRole('combobox',{name:'Task',exact:true}).selectOption('racing_game');
 await expect(input).toHaveValue('Make the steering smooth.\nKeep the car selection.');
 await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
 await page.locator('.revision-editor').screenshot({path:'../../results/reports/dashboard-prompt-editor-mobile.png'});
});

test('busy activity never locks typing and visible history stays bounded',async({page})=>{
 await editor(page,{working:true,large:true});const input=page.getByRole('textbox',{name:'Your update prompt',exact:true});
 await input.pressSequentially('Improve collisions and restart.');await page.waitForTimeout(2200);
 await expect(input).toHaveValue('Improve collisions and restart.');
 await expect(page.getByRole('button',{name:'Model is working',exact:true})).toBeDisabled();
 expect((await page.getByLabel('conversation stream').innerText()).length).toBeLessThan(125000);
 await expect(page.getByRole('link',{name:'Open full activity log',exact:true})).toBeVisible();
});

test('sending saves one request and clears only the submitted draft',async({page})=>{
 const {workspace,revision}=await editor(page);const sent:any[]=[];
 await page.route('**/api/workspaces/*/prompt',async route=>{sent.push(route.request().postDataJSON());revision.status='running';revision.prompts=[{update_id:'update-test',name:'Steering',prompt:sent[0].prompt,created:'2026-10-13T01:00:00Z',seconds:0,status:'running'}];await route.fulfill({json:{...workspace,revision}});});
 const input=page.getByRole('textbox',{name:'Your update prompt',exact:true});await input.fill('Make steering predictable.');
 await input.press('Control+Enter');await expect(page.getByText('Prompt saved. The model will update this working copy.',{exact:true})).toBeVisible();
 expect(sent).toEqual([{name:'',prompt:'Make steering predictable.'}]);await expect(input).toHaveValue('');
 await input.fill('Next: improve the camera.');await expect(input).toHaveValue('Next: improve the camera.');await expect(page.getByRole('button',{name:'Model is working',exact:true})).toBeDisabled();
});

test('a rejected request keeps the draft and explains the error',async({page})=>{
 await editor(page);await page.route('**/api/workspaces/*/prompt',route=>route.fulfill({status:503,json:{detail:'The local model service is unavailable. Your draft is still saved.'}}));
 const input=page.getByRole('textbox',{name:'Your update prompt',exact:true});await input.fill('Improve the race restart.');
 await page.getByRole('button',{name:'Run update',exact:true}).click();await expect(page.getByRole('alert')).toContainText('local model service is unavailable');await expect(input).toHaveValue('Improve the race restart.');
 await expect(page.getByRole('button',{name:'Run update',exact:true})).toBeEnabled();
});
