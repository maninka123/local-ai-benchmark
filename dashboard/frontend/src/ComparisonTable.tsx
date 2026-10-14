import {modelLabel} from './modelNames';
import {useEffect,useState} from 'react';
import type {ReactNode} from 'react';
import type {Run} from './types';
import RunTaskInfo from './RunTaskInfo';
import ScoreSummary from './ScoreSummary';
import ParameterSummary,{ModelSize} from './ParameterSummary';
import InputIcons from './InputIcons';

const columns=[
 {key:'model',label:'Model',width:414,sortable:true},
 {key:'parameters',label:'Calculated active parameters',width:342,sortable:true},
 {key:'start',label:'Task / date',width:306,sortable:true},
 {key:'review',label:'Output review',width:230,sortable:false},
 {key:'quality',label:'Automatic score status',width:290,sortable:true},
 {key:'complete',label:'Completion',width:200,sortable:true},
 {key:'speed',label:'Token speed',width:255,sortable:true},
 {key:'time',label:'Time taken',width:150,sortable:true},
 {key:'firstToken',label:'First token',width:140,sortable:false},
 {key:'memory',label:'Peak VRAM / RAM',width:205,sortable:false},
 {key:'tools',label:'Tools / failures',width:180,sortable:false},
] as const;
type ColumnKey=typeof columns[number]['key'];
const all=columns.map(c=>c.key),storageKey='local-llm-lab.comparison-columns.v1';
const fmt=(v:unknown,d=1)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(d):'—';
const gib=(v:unknown)=>typeof v==='number'?fmt(v/2**30):'—';
function initialColumns():ColumnKey[]{
 try{const saved=JSON.parse(localStorage.getItem(storageKey)??'null');if(Array.isArray(saved))return all.filter(key=>key==='model'||saved.includes(key));}catch{/* Storage is optional. */}
 return all;
}

export default function ComparisonTable({rows,sort,direction,onSort,onOpen}:{rows:Run[];sort:string;direction:number;onSort:(key:string)=>void;onOpen:(id:string)=>void}){
 const [shown,setShown]=useState<ColumnKey[]>(initialColumns);
 useEffect(()=>{try{localStorage.setItem(storageKey,JSON.stringify(shown));}catch{/* Storage is optional. */}},[shown]);
 const visible=columns.filter(c=>shown.includes(c.key));
 function toggle(key:ColumnKey){if(key==='model')return;setShown(previous=>previous.includes(key)?previous.filter(k=>k!==key):[...previous,key]);}
 function cells(r:Run):Record<ColumnKey,ReactNode>{return {
  model:<><div className="model-name-line"><InputIcons model={r.model}/><button className="model-link" title={r.model.name} onClick={()=>onOpen(r.run_id)}>{modelLabel(r.model.name)}</button></div><span className="model-quantization">{r.model.quantization}</span><ModelSize model={r.model}/></>,
  review:r.output_review?<><b>Final: {r.output_review.latest.score.toFixed(1)} / 100</b><small>Attempt {r.output_review.latest.number} · {r.output_review.latest.completed?'Complete':'Incomplete, partial credit'}</small><small>Earlier failed attempts are unscored.</small></>:<span>Separate review unavailable</span>,
  parameters:<ParameterSummary model={r.model}/>,start:<RunTaskInfo run={r}/>,quality:<ScoreSummary scores={r.scores} compact/>,
  complete:r.scores.complete?'Automatic checks passed; full review pending':'Partial / unverified',
  speed:<>Output speed: {fmt(r.performance.generation_tps)} tokens/s<small>Input speed: {fmt(r.performance.prompt_tps)} tokens/s</small></>,
  time:<>{fmt(r.task_seconds/60)} min<small>{fmt(r.task_seconds)} seconds</small>{r.after_updates?<><small>Initial: {fmt(r.after_updates.initial_seconds/60)} min</small><small>Further: {fmt(r.after_updates.extra_seconds/60)} min</small></>:null}</>,
  firstToken:<>{fmt(r.performance.ttft.median,3)} s</>,
  memory:<>{gib(r.performance.peak_vram_bytes)} / {gib(r.performance.peak_ram_bytes)} GiB</>,
  tools:<>{r.performance.tool_calls} / {r.performance.tool_failures}</>,
 };}
 return <><section className="comparison-controls" aria-label="Comparison table controls"><p role="status">{rows.length} matching attempts</p><details className="column-controls"><summary>Columns · {visible.length} of {columns.length} shown</summary><div className="column-options">{columns.map(c=><label key={c.key}><input type="checkbox" checked={shown.includes(c.key)} disabled={c.key==='model'} onChange={()=>toggle(c.key)}/>{c.label}{c.key==='model'?' (always visible)':''}</label>)}</div><div className="view-buttons"><button type="button" onClick={()=>setShown(all)}>Show all columns</button><button type="button" onClick={()=>setShown(['model','start','quality'])}>Essential columns</button></div><p className="scope-hint">Your column choices are remembered in this browser. Model stays visible so every result can be identified and opened.</p></details></section>
 <section className="table-wrap"><table style={{minWidth:visible.reduce((sum,c)=>sum+c.width,0)}}><caption>Attempt comparison · select a model name to inspect reports, code, screenshots and traces</caption><thead><tr>{visible.map(c=><th key={c.key} scope="col" className={`column-${c.key}`}>{c.sortable?<button onClick={()=>onSort(c.key)}>{c.label} {sort===c.key?(direction===1?'↑':'↓'):''}</button>:c.label}</th>)}</tr></thead><tbody>{rows.map(r=>{const values=cells(r);return <tr key={r.run_id}>{visible.map(c=><td key={c.key} className={`column-${c.key}`}>{values[c.key]}</td>)}</tr>;})}</tbody></table>{!rows.length?<p className="empty">No matching results yet. Choose Initial results, change the filters, or run an update from Model outputs.</p>:null}</section></>;
}
