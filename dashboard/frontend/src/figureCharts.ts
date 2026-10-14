import type {EChartsCoreOption} from 'echarts/core';
import type {Run} from './types';
import {itemStyle,taskLabel} from './chartStyles';
import type {ModelStyles} from './chartStyles';
import {modelLabel} from './modelNames';

export type FigureMode='all'|'model'|'task';
export type FigureGroup='Performance'|'Checks and quality'|'Resources and tools';
export const figureGroups:FigureGroup[]=['Performance','Checks and quality','Resources and tools'];
export type CompactBar={id:string;label:string;value:number|null;color:string;pattern?:string;detail:string};
export type FigureChart={title:string;subtitle:string;group:FigureGroup;option:EChartsCoreOption;height:number;emptyMessage?:string;bars?:CompactBar[];barMax?:number;unit?:string};
const escape=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!));
const number=(value:number)=>Number.isInteger(value)?String(value):value.toFixed(1);
const identity=(row:Run)=>[row.model.name,row.task,row.sensory_track??'',row.case??''].join('|');
type FigureRow=Run&{figureCases?:Run[][]};
const cohortKey=(row:Run)=>[row.model.name,row.task,row.sensory_track??'',...(row.task==='detective'?[row.protocol_hash,row.repetition]:[])].join('|');
const caseGroups=(rows:Run[])=>{const groups=new Map<string,Run[]>();for(const row of rows){const key=row.case??'unspecified',group=groups.get(key)??[];group.push(row);groups.set(key,group);}return [...groups.values()];};
const mean=(values:(number|null)[])=>{const recorded=values.filter((v):v is number=>typeof v==='number'&&Number.isFinite(v));return recorded.length?recorded.reduce((sum,v)=>sum+v,0)/recorded.length:null;};
const measurement=(row:FigureRow,value:(row:Run)=>number|null)=>row.figureCases?mean(row.figureCases.map(group=>mean(group.map(value)))):mean([value(row)]);
function caseNote(row:FigureRow,value?:(row:Run)=>number|null){
 if(!row.figureCases)return '';
 const groups=row.figureCases,available=value?groups.filter(group=>mean(group.map(value))!==null).length:groups.length;
 const failures=groups.flat().filter(r=>r.status==='failed'||r.after_updates?.status==='failed').length;
 return `Case average · ${available}/${groups.length} cases${value?' with recorded values':''} · equal weight per case${failures?` · ${failures} failed attempts included where recorded`:''}`;
}
export function detectiveCaseAverages(rows:Run[]):FigureRow[]{
 const grouped=new Map<string,Run[]>();
 for(const row of rows){if(row.task!=='detective')continue;const key=cohortKey(row);const group=grouped.get(key)??[];group.push(row);grouped.set(key,group);}
 const seen=new Set<string>();
 return rows.flatMap(row=>{
  if(row.task!=='detective')return [row];
  const key=cohortKey(row);if(seen.has(key))return [];seen.add(key);
  const group=grouped.get(key)!,cases=caseGroups(group);
  return cases.length>1?[{...group[0],run_id:`case-average:${key}`,case:null,status:'case_average',figureCases:cases}]:group;
 });
}

export function figureLabels(rows:FigureRow[],mode:FigureMode):string[]{
 const groups=new Map<string,Run[]>();
 for(const row of rows){const key=identity(row);const group=groups.get(key)??[];group.push(row);groups.set(key,group);}
 for(const group of groups.values())group.sort((a,b)=>a.start.localeCompare(b.start)||a.run_id.localeCompare(b.run_id));
 return rows.map(row=>{
  const parts=[mode!=='model'?modelLabel(row.model.name):'',mode!=='task'?taskLabel(row):row.task==='detective'?(row.sensory_track==='text_only_detective'?'Text only':'Visual'):'',row.figureCases?`Average · ${row.figureCases.length} cases`:row.case?.replaceAll('_',' ')??''].filter(Boolean);
  const group=groups.get(identity(row))!;
  if(group.length>1)parts.push(`Attempt ${group.findIndex(r=>r.run_id===row.run_id)+1}`);
  if(row.status==='failed')parts.push('Failed');
  return parts.join(mode==='all'?'\n':' · ')||'Attempt';
 });
}

type BarOptions={max?:number;ascending?:boolean;detail?:(row:FigureRow)=>string};
function horizontalBar(rows:FigureRow[],value:(row:FigureRow)=>number|null,unit:string,mode:FigureMode,fills:ModelStyles,settings:BarOptions={}){
 const ordered=[...rows].sort((a,b)=>{
  const av=value(a),bv=value(b);
  if(av===null)return bv===null?0:1;if(bv===null)return -1;
  return (settings.ascending?av-bv:bv-av)||a.start.localeCompare(b.start)||a.run_id.localeCompare(b.run_id);
 });
 const labels=figureLabels(ordered,mode),visible=Math.min(ordered.length,14);
 const option:EChartsCoreOption={
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},confine:true,formatter:(input:{dataIndex:number}[]|{dataIndex:number})=>{
   const point=Array.isArray(input)?input[0]:input;
   if(!point||!ordered[point.dataIndex])return '';
   const row=ordered[point.dataIndex],v=value(row);
   return `<b>${escape(modelLabel(row.model.name))}</b><br/>${escape(taskLabel(row)+(row.case?' · '+row.case.replaceAll('_',' '):''))}<br/>${v===null?'Not recorded':number(v)+' '+escape(unit)}${settings.detail?'<br/>'+escape(settings.detail(row)):''}<br/><span style="color:#64748b">${escape(row.model.name)}</span>`;
  }},
  grid:{left:235,right:76,top:12,bottom:55,containLabel:false},
  xAxis:{type:'value',min:0,max:settings.max,name:unit,nameLocation:'middle',nameGap:30,splitNumber:3,axisLine:{show:false},axisTick:{show:false},splitLine:{lineStyle:{color:'#e9edf2',type:'dashed'}}},
  yAxis:{type:'category',inverse:true,data:labels,axisLine:{show:false},axisTick:{show:false},axisLabel:{fontSize:16,lineHeight:22,width:215,overflow:'break',margin:12,interval:0}},
  dataZoom:ordered.length>14?[{type:'inside',yAxisIndex:0,startValue:0,endValue:13,zoomOnMouseWheel:false,moveOnMouseWheel:true,preventDefaultMouseMove:false},{type:'slider',yAxisIndex:0,right:0,width:12,startValue:0,endValue:13,showDetail:false}]:[],
  series:[{type:'bar',name:unit,barMaxWidth:24,label:{show:true,position:'right',fontSize:16,color:'#374151',formatter:(p:{value:number|null})=>p.value===null?'':number(p.value)},data:ordered.map(row=>({value:value(row),itemStyle:{...itemStyle(row,fills),borderRadius:[0,4,4,0]}}))}],
 };
 const bars=ordered.map((row,index)=>({id:row.run_id,label:labels[index],value:value(row),color:itemStyle(row,fills).color,pattern:fills[row.model.name]?.css,detail:`${row.model.name} · ${taskLabel(row)}${row.figureCases?'':' · '+row.start}${settings.detail?' · '+settings.detail(row):''}`}));
 const rowHeight=Math.max(mode==='all'?76:52,...labels.map(label=>label.split('\n').reduce((lines,line)=>lines+Math.max(1,Math.ceil(line.length/24)),0)*22+12));
 return {option,bars,unit,barMax:settings.max??Math.max(1,...ordered.map(row=>value(row)??0)),height:Math.max(390,visible*rowHeight+70),emptyMessage:rows.some(row=>value(row)!==null)?undefined:rows.length?'This measurement was not recorded for these attempts.':'No attempts match this selection.'};
}

export function buildFigureCharts(rows:Run[],mode:FigureMode,fills:ModelStyles):FigureChart[]{
 const averaged=detectiveCaseAverages(rows);
 const bar=(title:string,subtitle:string,group:FigureGroup,value:(r:Run)=>number|null,unit:string,settings:BarOptions={}):FigureChart=>({title,subtitle,group,...horizontalBar(averaged,row=>measurement(row,value),unit,mode,fills,{...settings,detail:row=>[caseNote(row,value),settings.detail?.(row)].filter(Boolean).join(' · ')})});
 const groups=new Map<string,Run[]>();
 for(const row of rows){const key=cohortKey(row);const group=groups.get(key)??[];group.push(row);groups.set(key,group);}
 const completionRows:FigureRow[]=[],rates=new Map<string,{passed:number;total:number;pending:number;percent:number|null}>();
 for(const group of groups.values()){
  const scored=group.filter(r=>!r.after_updates||r.after_updates.scored);
  const cases=caseGroups(group),row={...group[0],case:null,...(group[0].task==='detective'&&cases.length>1?{run_id:`case-average:${cohortKey(group[0])}`,status:'case_average',figureCases:cases}:{})};
  const rate=(items:Run[])=>{const evaluated=items.filter(r=>!r.after_updates||r.after_updates.scored);return evaluated.length?100*evaluated.filter(r=>r.scores.complete).length/evaluated.length:null;};
  completionRows.push(row);rates.set(row.run_id,{passed:scored.filter(r=>r.scores.complete).length,total:scored.length,pending:group.length-scored.length,percent:row.figureCases?mean(cases.map(rate)):rate(group)});
 }
 const completion={title:'Automatic checks passed',subtitle:'Share passing checks · Detective rates averaged by case · full review remains separate',group:'Checks and quality' as const,...horizontalBar(completionRows,row=>rates.get(row.run_id)!.percent,'%',mode,fills,{max:100,detail:row=>{const rate=rates.get(row.run_id)!;return `${caseNote(row)}${row.figureCases?' · ':''}${rate.passed} / ${rate.total} scored attempts passed${rate.pending?` · ${rate.pending} awaiting evaluation`:''}`;} })};
 const eligible=(r:Run)=>typeof r.performance.generation_tps==='number'&&Number.isFinite(r.performance.generation_tps)&&(!r.after_updates||r.after_updates.scored);
 const scatterRows=averaged.map(row=>({row,speed:measurement(row,r=>eligible(r)?r.performance.generation_tps:null),points:measurement(row,r=>eligible(r)?r.scores.verified_points:null)})).filter(r=>r.speed!==null&&r.points!==null);
 const scatter:FigureChart={title:'Speed and verified points',subtitle:'Tokens per second vs. verified points · higher is better on both axes',group:'Checks and quality',height:450,emptyMessage:scatterRows.length?undefined:'No scored attempts with generation speed are available.',option:{
  tooltip:{confine:true,formatter:(p:{dataIndex:number})=>{const sample=scatterRows[p.dataIndex],row=sample.row;return `<b>${escape(modelLabel(row.model.name))}</b><br/>${escape(taskLabel(row)+(row.case?' · '+row.case.replaceAll('_',' '):''))}<br/>${number(sample.speed!)} tokens/s · ${number(sample.points!)} verified points<br/>${escape(row.figureCases?caseNote(row,r=>eligible(r)?r.performance.generation_tps:null):row.start)}`; }},
  grid:{left:15,right:25,top:20,bottom:70,containLabel:true},
  xAxis:{type:'value',name:'Tokens / second',nameLocation:'middle',nameGap:35,splitNumber:3},
  yAxis:{type:'value',name:'Verified points',min:0,max:100,splitNumber:4},
  series:[{type:'scatter',symbolSize:18,data:scatterRows.map(r=>({name:figureLabels([r.row],mode)[0],value:[r.speed,r.points],itemStyle:{...itemStyle(r.row,fills),borderColor:'#fff',borderWidth:1.5,opacity:.9}}))}],
 }};
 return [
  bar('Generation speed','Output tokens per second · higher is faster','Performance',r=>r.performance.generation_tps,'tokens/s'),
  bar('Prompt processing','Input tokens per second · higher is faster','Performance',r=>r.performance.prompt_tps,'tokens/s'),
  bar('Time taken','Elapsed minutes · includes partial and failed attempts','Performance',r=>r.task_seconds/60,'minutes',{ascending:true}),
  bar('First token latency','Median seconds to first token · lower is faster','Performance',r=>r.performance.ttft.median,'seconds',{ascending:true}),
  bar('Verified points','Points out of 100 · lower bound until full quality review','Checks and quality',r=>r.after_updates&&!r.after_updates.scored?null:r.scores.verified_points,'points',{max:100}),
  scatter,completion,
  bar('Peak VRAM','Device memory in GiB · lower uses less memory','Resources and tools',r=>r.performance.peak_vram_bytes===null?null:r.performance.peak_vram_bytes/2**30,'GiB',{ascending:true}),
  bar('Peak RAM','System memory in GiB · lower uses less memory','Resources and tools',r=>r.performance.peak_ram_bytes===null?null:r.performance.peak_ram_bytes/2**30,'GiB',{ascending:true}),
  bar('Tool calls','Calls per attempt','Resources and tools',r=>r.performance.tool_calls,'calls'),
  bar('Tool failures','Failed calls per attempt · lower is better','Resources and tools',r=>r.performance.tool_failures,'failures',{ascending:true}),
 ];
}
