import {useEffect,useState} from 'react';
import {JudgmentDetails} from './JudgedResults';
import type {Judgment} from './JudgedResults';
import GamePreview from './GamePreview';
import {SavedOutputActions} from './OutputDialog';
import {modelLabel} from './modelNames';

type Attempt={judgment?:Judgment;number:number;name:string;outcome:string;readiness:string;error:string|null;basis:string};
type Repair={repair_id:string;model:string;task:string;configured_model:string;source_changed_lines:number;runnable:boolean;completion?:boolean;changes_summary:string|string[];limitations?:string[];files:string[];verification?:{check:string;passed?:boolean}[]};
type History={attempts:Attempt[];repairs:Repair[];other_saved_updates:number;note:string};
function RepairOutput({repair,runId}:{repair:Repair;runId:string}){
 const [file,setFile]=useState(''),[text,setText]=useState<string|null>(null);
 const drivingVerified=repair.verification?.some(v=>v.check==='Isolated real WASD movement and steering'&&v.passed===true);
 const url=`/api/outputs/${encodeURIComponent(runId)}/repairs/${repair.repair_id}/file/${file.split('/').map(encodeURIComponent).join('/')}`;
 useEffect(()=>{setText(null);if(!file||/\.(png|jpe?g|md)$/i.test(file))return;const controller=new AbortController();fetch(url,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('File unavailable');return r.text();}).then(setText).catch(e=>{if(e.name!=='AbortError')setText('This saved file could not load.');});return()=>controller.abort();},[file,url]);
 return <article className="small-repair"><h4>Small repair · {repair.runnable?(repair.task==='racing_game'?'Preview opens':'Script runs'): 'Not runnable'}</h4><p><b>Configured repair model: {repair.configured_model==='gpt-6.1-sol'?'GPT-6.1 Sol':repair.configured_model}</b><br/>{repair.source_changed_lines} source lines changed · fewer than 50 · saved separately</p><p>{Array.isArray(repair.changes_summary)?repair.changes_summary.join(' '):repair.changes_summary}</p><p className="scope-hint">{repair.completion?'Repair review confirms completion.':'The full task remains incomplete. Original outputs, scores and attempt labels are preserved.'}</p>{repair.limitations?.length?<details><summary>Remaining limitations</summary><ul>{repair.limitations.map((v,i)=><li key={i}>{v}</li>)}</ul></details>:null}
  {repair.task==='racing_game'?<GamePreview endpoint={`/api/outputs/${encodeURIComponent(runId)}/repairs/${repair.repair_id}/game`} available={repair.runnable} title="Separately repaired local preview" modelName={modelLabel(repair.model)} issue={drivingVerified?'WASD movement and steering verified. Small GPT-6.1 Sol repair; the full race remains incomplete.':'Static preview only; driving remains unavailable. Small GPT-6.1 Sol repair; the full race remains incomplete.'}/>:null}
  {repair.files.length?<><label>Repaired output file<select value={file} onChange={e=>setFile(e.target.value)}><option value="">Select a repaired output</option>{repair.files.filter(f=>!f.startsWith('game/dist/')).map(f=><option key={f}>{f}</option>)}</select></label>{file?<SavedOutputActions key={file} title="Separately repaired output" file={file} text={text} url={url}/>:null}</>:null}
 </article>;
}

export default function AttemptHistory({runId,view}:{runId:string;view:'initial'|'further'}){
 const [data,setData]=useState<History|null>(null),[error,setError]=useState('');
 useEffect(()=>{setData(null);setError('');const controller=new AbortController();async function refresh(){try{const response=await fetch(`/api/outputs/${encodeURIComponent(runId)}/history`,{signal:controller.signal});if(!response.ok)throw Error('Attempt history could not load.');const value=await response.json();if(!controller.signal.aborted){setData(value);setError('');}}catch(e){if(!controller.signal.aborted)setError((e as Error).message);}}void refresh();const timer=setInterval(refresh,15000);return()=>{controller.abort();clearInterval(timer);};},[runId]);
 const items=data?.attempts.filter(a=>view==='initial'?a.number===1:a.number>1)??[];
 return <section className="attempt-history" aria-label="Attempt outcomes"><h3>{view==='initial'?'Initial attempt outcome':'Further work attempt outcomes'}</h3>{error?<p role="alert">{error}</p>:null}{!data?<p role="status">Loading attempt outcomes…</p>:<><div className="attempt-outcomes">{items.map(a=><article key={a.number} className={`attempt-outcome attempt-${a.outcome}`}><h4>Attempt {a.number} · {a.name}</h4><strong>{a.outcome==='complete'?'Completed successfully':a.outcome==='failed'?'Failed to complete':a.outcome==='working'?'In progress':'Completion review pending'}</strong><p>{a.readiness}</p>{a.judgment?<JudgmentDetails review={a.judgment}/>:null}{a.error?<p className="error">Execution error: {a.error}</p>:null}{a.basis?<details><summary>Why this status?</summary><p>{a.basis}</p></details>:null}</article>)}</div>{!items.length?<p>No benchmark improvement attempt is saved yet.</p>:null}<p className="scope-hint">{data.note}{data.other_saved_updates?` ${data.other_saved_updates} other manual/setup requests are saved in the prompt history.`:''}</p>{view==='further'?data.repairs.map(repair=><RepairOutput key={repair.repair_id} repair={repair} runId={runId}/>):null}</>}</section>;
}
