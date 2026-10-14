import type {Run,Summary} from './types';
export const overviewMetrics={
 score:{label:'Final task score',unit:'points / 100',better:'Higher',max:100},
 quality:{label:'Output quality before attempt band',unit:'points / 100',better:'Higher',max:100},
 outputSpeed:{label:'Output token speed',unit:'tokens/s',better:'Higher'},
 inputSpeed:{label:'Input token speed',unit:'tokens/s',better:'Higher'},
 size:{label:'Installed model size',unit:'GB',better:'Smaller'},
 active:{label:'Calculated active parameters',unit:'billion parameters',better:'Size'},
 reportedActive:{label:'Reported active parameters',unit:'billion parameters',better:'Size'},
 parameters:{label:'Total model parameters',unit:'billion parameters',better:'Size'},
 activeSize:{label:'Estimated active weight size',unit:'GB',better:'Smaller'},
 initialTime:{label:'Initial task time',unit:'minutes',better:'Lower'},
 totalTime:{label:'Total time including further work',unit:'minutes',better:'Lower'},
} as const;
export type OverviewMetric=keyof typeof overviewMetrics;
export type OverviewPoint={id:string;model:string;track:string;cases:number;values:Record<OverviewMetric,number|null>;recorded:Record<OverviewMetric,number>};
const finite=(v:unknown):number|null=>typeof v==='number'&&Number.isFinite(v)&&v>=0?v:null;
const mean=(v:(number|null)[])=>{const numbers=v.filter((n):n is number=>n!==null);return numbers.length?numbers.reduce((s,n)=>s+n,0)/numbers.length:null;};
export function overviewPoints(rows:Run[],revisions:Summary['modifications'],task:string):OverviewPoint[]{
 const groups=new Map<string,Run[]>();
 for(const row of rows){if(row.task!==task||!row.output_review)continue;const key=[row.model.name,row.sensory_track??''].join('|');groups.set(key,[...(groups.get(key)??[]),row]);}
 const extra=new Map<string,number>();for(const r of revisions)extra.set(r.base_run_id,(extra.get(r.base_run_id)??0)+(r.extra_seconds??r.generation_seconds));
 return [...groups.entries()].map(([id,group])=>{
  const cases=new Map<string,Run[]>();for(const r of group)cases.set(r.case??r.run_id,[...(cases.get(r.case??r.run_id)??[]),r]);
  const value=(r:Run,key:OverviewMetric):number|null=>{
   const m=r.model,p=m.parameter_comparison?.calculated,review=r.output_review!.latest;
   const all=(p?.total??0)+(p?.auxiliary_parameters??0);
   const values:Record<OverviewMetric,number|null>={score:finite(review.score),quality:finite(review.raw_score),outputSpeed:finite(r.performance.generation_tps),inputSpeed:finite(r.performance.prompt_tps),size:finite(m.size/1e9),active:typeof p?.active==='number'?finite(p.active/1e9):null,reportedActive:typeof (m.active_parameters??m.parameter_comparison?.reported.active)==='number'?finite((m.active_parameters??m.parameter_comparison!.reported.active!)/1e9):null,parameters:typeof (p?.total??m.parameter_count)==='number'?finite((p?.total??m.parameter_count!)/1e9):null,activeSize:typeof p?.active==='number'&&all>0?finite(m.size/1e9*p.active/all):null,initialTime:finite((r.after_updates?.initial_seconds??r.task_seconds)/60),totalTime:finite((r.after_updates?r.task_seconds:r.task_seconds+(extra.get(r.run_id)??0))/60)};
   return values[key];
  };
  const values={} as OverviewPoint['values'],recorded={} as OverviewPoint['recorded'];
  for(const key of Object.keys(overviewMetrics) as OverviewMetric[]){const v=[...cases.values()].map(c=>mean(c.map(r=>value(r,key))));values[key]=mean(v);recorded[key]=v.filter(n=>n!==null).length;}
  return {id,model:group[0].model.name,track:group[0].sensory_track??'',cases:cases.size,values,recorded};
 });
}
