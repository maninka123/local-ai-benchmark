import {memo,useEffect,useState} from 'react';

type Draft={name:string;prompt:string};
type Props={runId:string;loading:boolean;paused:boolean;working:boolean;busy:boolean;onSend:(name:string,prompt:string)=>Promise<boolean>};
const draftKey=(id:string)=>`local-llm-prompt-draft:${id}`;
function loadDraft(id:string):Draft{
 try{const saved=JSON.parse(sessionStorage.getItem(draftKey(id))??'null');if(typeof saved?.name==='string'&&typeof saved?.prompt==='string')return saved;}catch{/* Storage is optional. */}
 return {name:'',prompt:''};
}

export default memo(function PromptComposer({runId,loading,paused,working,busy,onSend}:Props){
 const [draft,setDraft]=useState<Draft>(()=>loadDraft(runId));
 useEffect(()=>{try{if(draft.name||draft.prompt)sessionStorage.setItem(draftKey(runId),JSON.stringify(draft));else sessionStorage.removeItem(draftKey(runId));}catch{/* Keep the editor usable without browser storage. */}},[runId,draft]);
 const canSend=!loading&&!paused&&!working&&!busy&&!!draft.prompt.trim();
 const reason=paused?'Processing is paused and models are unloaded. You can prepare your next prompt here.':loading?'Loading this working copy…':working?'The current update is still running. You can write your next prompt while you wait.':'Your prompt updates the Further work copy. Initial results stay saved.';
 async function submit(event:React.FormEvent){
  event.preventDefault();if(!canSend)return;
  const submitted={...draft};
  if(await onSend(submitted.name,submitted.prompt))setDraft(current=>current.name===submitted.name&&current.prompt===submitted.prompt?{name:'',prompt:''}:current);
 }
 return <section className="revision-editor"><div className="composer-heading"><h3>Ask the model to update</h3><span className="draft-state">{draft.prompt||draft.name?'Draft saved in this browser':'Write a new prompt'}</span></div>
  <form onSubmit={submit}><label htmlFor="update-prompt">Your update prompt</label><div className="terminal-input"><span aria-hidden="true">❯</span><textarea id="update-prompt" value={draft.prompt} onChange={event=>setDraft(current=>({...current,prompt:event.target.value}))} onKeyDown={event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();if(canSend)event.currentTarget.form?.requestSubmit();}}} maxLength={20000} rows={4} placeholder="What should change? Describe the problem and the result you want." aria-describedby="prompt-guidance" spellCheck={false}/></div>
  <p id="prompt-guidance" className="scope-hint composer-guidance">{reason}</p><div className="terminal-input-actions"><details><summary>Update title (optional)</summary><label>Update title<input value={draft.name} onChange={event=>setDraft(current=>({...current,name:event.target.value}))} maxLength={100} placeholder="Smoother steering"/></label></details><div className="composer-buttons"><button type="button" onClick={()=>setDraft({name:'',prompt:''})} disabled={!draft.prompt&&!draft.name||busy}>Clear draft</button><button type="submit" disabled={!canSend}>{busy?'Saving…':paused?'Processing paused':working?'Model is working':'Run update'}</button></div></div></form>
  <p className="scope-hint">Enter adds a new line · Ctrl/⌘ + Enter sends · 60-minute limit per prompt</p>
 </section>;
});
