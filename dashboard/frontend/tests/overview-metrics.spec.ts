import {test,expect} from '@playwright/test';
import {overviewPoints} from '../src/overviewMetrics';
import type {Run,Summary} from '../src/types';
function row(id:string,caseId:string,score:number,speed:number|null):Run{return {run_id:id,task:'detective',case:caseId,sensory_track:'native_multimodal',task_seconds:120,model:{name:'m',size:20e9,active_parameters:null,parameter_comparison:{calculated:{active:4e9,total:20e9,auxiliary_parameters:5e9},reported:{active:null}}},output_review:{initial:{score,raw_score:score,completed:false},latest:{number:3,score:score+5,raw_score:score+5,completed:false}},performance:{generation_tps:speed,prompt_tps:null}} as Run;}
test('Detective averages cases equally and keeps missing speeds unavailable',()=>{
 const result=overviewPoints([row('a','case01',10,null),row('b','case01',30,null),row('c','case02',40,10)],[],'detective')[0];
 expect(result.values.score).toBe(35);expect(result.values.outputSpeed).toBe(10);expect(result.recorded.outputSpeed).toBe(1);expect(result.cases).toBe(2);expect(result.values.reportedActive).toBeNull();expect(result.values.activeSize).toBe(3.2);
});
test('Combined time includes saved updates exactly once and stage scores stay distinct',()=>{
 const original=row('a','case01',10,0),revision={base_run_id:'a',generation_seconds:60,extra_seconds:180} as Summary['modifications'][number];
 const initial=overviewPoints([original],[revision],'detective')[0];expect(initial.values.totalTime).toBe(5);expect(initial.values.initialTime).toBe(2);expect(initial.values.score).toBe(15);expect(initial.values.outputSpeed).toBe(0);
 const updated={...original,task_seconds:300,after_updates:{initial_seconds:120,extra_seconds:180,status:'evaluated',scored:true}};
 const further=overviewPoints([updated],[revision],'detective')[0];expect(further.values.totalTime).toBe(5);expect(further.values.score).toBe(15);
});
test('Setup-only rows and other tasks do not become fake zero-score models',()=>{
 const r=row('a','case01',10,null);expect(overviewPoints([{...r,output_review:undefined}],[],'detective')).toEqual([]);expect(overviewPoints([r],[],'racing_game')).toEqual([]);
});
