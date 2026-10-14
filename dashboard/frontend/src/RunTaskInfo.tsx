import type {Run} from './types';
import {taskLabel} from './chartStyles';
export default function RunTaskInfo({run}:{run:Run}){
 const settings=run.config as {benchmark?:{task_timeout_seconds?:number}};
 const limit=settings?.benchmark?.task_timeout_seconds;
 const started=new Intl.DateTimeFormat('en-AU',{timeZone:'Australia/Sydney',dateStyle:'medium',timeStyle:'short'}).format(new Date(run.start));
 return <div className="task-info"><b>{taskLabel(run)}</b>{run.case?<span>{run.case.replace('_',' ')}</span>:null}<small>{run.after_updates?'Update requested':'Started'}: {started} (Sydney)<br/>Attempt {run.repetition}<br/><span>{run.after_updates?(run.after_updates.status==='finished'?(run.after_updates.scored?'Updated and re-evaluated':'Updated ? awaiting re-evaluation'):run.after_updates.status.replaceAll('_',' ')):(run.status==='evaluated'?'Finished and scored':run.status==='failed'?'Test stopped or failed':'Test interrupted')}</span><br/>Set time limit: {limit?`${limit/60} minutes`:'Unavailable'}<br/>{run.after_updates?'Total time':'Time taken'}: {(run.task_seconds/60).toFixed(1)} minutes</small></div>;
}
