import {useEffect,useRef,useState} from 'react';
import OutputDialog from './OutputDialog';

type ReferenceTask={id:string;title:string;summary:string;action:string;available:boolean;status:Record<string,unknown>;context:Record<string,unknown>;prompt:string;system_prompt:string;original_prompt_matches:boolean;prompt_sha256:string|null;output_url:string|null;folder:string;verification:Record<string,unknown>};
type References={model:string;reasoning:string;mode:string;comparison_note:string;tasks:ReferenceTask[]};
type SavedFile={path:string;bytes:number;url:string};

function ReferenceTaskView({task}:{task:ReferenceTask}){
 const [preview,setPreview]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[files,setFiles]=useState<SavedFile[]|null>(null),[filesLoading,setFilesLoading]=useState(false);
 const alive=useRef(true);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 async function openFolder(){setError('');try{const response=await fetch(`/api/references/${task.id}/open-folder`,{method:'POST'});const data=await response.json();if(!response.ok)throw Error(data.detail||'Folder could not open.');if(alive.current)setMessage('Opened the saved reference folder.');}catch(e){if(alive.current)setError((e as Error).message);}}
 async function loadFiles(){if(files!==null||filesLoading)return;setFilesLoading(true);setError('');try{const response=await fetch(`/api/references/${task.id}/files`);if(!response.ok)throw Error('Supporting files could not load. Close and reopen this section to retry.');const data=await response.json();if(alive.current)setFiles(data);}catch(e){if(alive.current)setError((e as Error).message);}finally{if(alive.current)setFilesLoading(false);}}
 return <article className="reference-detail" aria-label={`${task.title} reference`}>
  <div className="reference-title"><div><p className="eyebrow">ORIGINAL TASK · ASTRA HIGH</p><h3>{task.title}</h3></div><span className={`reference-state ${task.available?'ready':''}`}>{task.available?'Ready to open':'Being prepared'}</span></div>
  <h4>What the model was asked to do</h4><p className="reference-summary">{task.summary}</p>
  {task.id==='detective'?<p className="scope-hint">All three supplied cases appear in one investigation report. Each case uses its own public images and documents.</p>:null}
  <div className="reference-actions">{task.available&&task.output_url?<><button className="reference-primary" type="button" onClick={()=>setPreview(true)}>{task.action}</button><a href={task.output_url} target="_blank" rel="noopener noreferrer">Open in browser</a></>:<button type="button" disabled>Output is being prepared</button>}<button type="button" onClick={openFolder}>Open saved folder</button></div>
  {message?<p role="status" className="scope-hint">{message}</p>:null}{error?<p role="alert" className="error">{error}</p>:null}
  {preview&&task.output_url?<OutputDialog title={`${task.title} - GPT-6 Astra High`} url={task.output_url} scripts onClose={()=>setPreview(false)} hint={task.id==='racing_game'?'Click inside to play. W/A/S/D or arrows drive; C changes camera; P pauses; R restarts.':'Read the saved reference report. Close the popup to return to the task selection.'}/>:null}
  <details className="reference-prompt"><summary>Read the full original prompt</summary><p className="scope-hint">{task.original_prompt_matches?'Exact saved copy of the benchmark task prompt.':'Prompt copy is being prepared or needs verification.'} The summary above is only for navigation.</p><pre>{task.prompt||'The prompt will appear when its saved copy is available.'}</pre><details><summary>Shared evaluation instructions</summary><pre>{task.system_prompt||'Shared instructions are being prepared.'}</pre></details></details>
  <details onToggle={event=>{if(event.currentTarget.open)void loadFiles();}}><summary>Supporting files and saved folder</summary><p className="reference-path">{task.folder}</p>{filesLoading?<p role="status">Loading files…</p>:files?.length?<ul className="reference-files">{files.map(file=><li key={file.path}><a href={file.url} target="_blank" rel="noopener noreferrer">{file.path}</a><span>{file.bytes<1024?`${file.bytes} B`:`${(file.bytes/1024).toFixed(1)} KB`}</span></li>)}</ul>:<p>Supporting files are still being prepared.</p>}</details>
  <details><summary>How this reference was produced and checked</summary><p>One original task prompt, with tools for reading the inputs, creating files, running code and checking the result. Testing and debugging within that assignment are included. This is not a single inference call. Any resumed execution is recorded below.</p><p>Model: <strong>gpt-6-astra</strong> · Reasoning: <strong>High</strong>. Local benchmark scores and timings stay separate.</p><h4>Saved checks</h4><pre className="reference-json">{Object.keys(task.verification).length?JSON.stringify(task.verification,null,2):'Verification is in progress.'}</pre><h4>Execution record</h4><pre className="reference-json">{JSON.stringify(task.context,null,2)}</pre><p className="reference-path">Original prompt SHA-256: {task.prompt_sha256??'Pending'}</p></details>
 </article>;
}

export default function ReferenceResults(){
 const [data,setData]=useState<References|null>(null),[selected,setSelected]=useState('racing_game'),[error,setError]=useState('');
 useEffect(()=>{const controller=new AbortController();async function refresh(){try{const response=await fetch('/api/references',{signal:controller.signal});if(!response.ok)throw Error('Reference results could not load. Retrying shortly.');const value=await response.json();if(!controller.signal.aborted){setData(value);setError('');}}catch(e){if(!controller.signal.aborted)setError((e as Error).message);}}void refresh();const timer=setInterval(refresh,15000);return()=>{controller.abort();clearInterval(timer);};},[]);
 const task=data?.tasks.find(t=>t.id===selected);
 return <section className="reference-results" aria-label="Astra reference results"><div className="reference-heading"><div><p className="eyebrow">FRONTIER MODEL · REFERENCE OUTPUTS</p><h2>GPT-6 Astra <span>High</span></h2><p>One place to play, read and inspect the three reference tasks.</p></div><span className="reference-count">{data?.tasks.filter(t=>t.available).length??0} / 3 ready</span></div>
  <p className="reference-note">{data?.comparison_note??'Original benchmark prompts, saved separately as frontier reference outputs.'}</p>
  {error?<p role="alert" className="error">{error}</p>:null}
  {!data?<p role="status">Loading references…</p>:<><div className="reference-choices" aria-label="Choose a reference task">{data.tasks.map((item,index)=><button type="button" key={item.id} aria-pressed={selected===item.id} onClick={()=>setSelected(item.id)}><span className="reference-number" aria-hidden="true">0{index+1}</span><strong>{item.title}</strong><span>{item.available?'Open the reference':'Being prepared'}</span></button>)}</div>{task?<ReferenceTaskView key={task.id} task={task}/>:null}</>}
 </section>;
}
