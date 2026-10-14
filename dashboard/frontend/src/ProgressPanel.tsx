import {modelLabel} from './modelNames';
import type {Progress} from './types';
const duration=(seconds:number)=>`${Math.floor(seconds/60)}m ${Math.floor(seconds%60).toString().padStart(2,'0')}s`;
export default function ProgressPanel({progress}:{progress:Progress}){
 const current=progress.current;
 return <section className="progress-panel" aria-label="Benchmark progress">
  <article className="progress-card"><div className="progress-heading"><h2>Overall progress</h2><strong>{Math.round(progress.percent)}%</strong></div>
   <progress aria-label="Overall progress" value={progress.finished} max={Math.max(1,progress.total)}/>
   <p><b>{progress.finished} of {progress.total}</b> attempts finished · {progress.retries} timeout retries included</p>
   <span className="status-pill">{progress.state==='running'?'Running · one model at a time':progress.state==='complete'?'Finished':progress.state==='stopped'?'Stopped by you':progress.state==='waiting_downloads'?'Downloading added models':progress.state==='interrupted'?'Interrupted · ready to resume':'Updating the task queue'}</span>
  </article>
  <article className="progress-card"><div className="progress-heading"><h2>Current task progress</h2><strong>{current?`${Math.floor(current.budget_percent)}%`:'—'}</strong></div>
   <progress aria-label="Current task time budget" value={current?.budget_percent??0} max={100}/>
   {current?<><p className="current-model"><b title={current.model}>{modelLabel(current.model)}</b><br/>{current.task.replaceAll('_',' ')} {current.case?.replaceAll('_',' ')}</p><p>{current.stage} · {current.completed_calls}/{current.max_calls} model calls completed</p><p className="progress-note">{duration(current.elapsed_seconds)} elapsed / {Math.round(current.limit_seconds/60)} minutes allowed. Bar shows time used, not estimated completion.</p></>:<p className="progress-note">{progress.state==='complete'?'All queued attempts have finished.':progress.state==='stopped'?'Tests stopped. Saved results and partial files are retained.':'Waiting for the next task to start.'}</p>}
  </article>
 </section>;
}
