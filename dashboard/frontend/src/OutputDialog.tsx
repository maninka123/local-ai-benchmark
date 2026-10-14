import {useLayoutEffect,useId,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import type {ReactNode} from 'react';

export default function OutputDialog({title,url,children,hint,scripts=false,loading=false,error='',onClose,onRetry,onOpenBrowser}:{title:string;url?:string;children?:ReactNode;hint?:string;scripts?:boolean;loading?:boolean;error?:string;onClose:()=>void;onRetry?:()=>void;onOpenBrowser?:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null),content=useRef<HTMLDivElement>(null),heading=useId();
 const [fullscreenError,setFullscreenError]=useState(''),[frameReady,setFrameReady]=useState(false);
 useLayoutEffect(()=>{
  const element=dialog.current,previous=document.activeElement as HTMLElement|null,overflow=document.body.style.overflow;
  element?.showModal();document.body.style.overflow='hidden';setFrameReady(true);
  return()=>{element?.close();document.body.style.overflow=overflow;if(previous?.isConnected)previous.focus();};
 },[]);
 async function fullscreen(){try{if(!content.current?.requestFullscreen)throw Error();await content.current.requestFullscreen();setFullscreenError('');}catch{setFullscreenError('Fullscreen is unavailable. Use Open in browser for a larger view.');}}
 return createPortal(<dialog ref={dialog} className="output-dialog" aria-labelledby={heading} onCancel={event=>{event.preventDefault();onClose();}} onClick={event=>{if(event.target===event.currentTarget)onClose();}}>
  <section className="output-dialog-shell">
   <header className="output-dialog-header"><h2 id={heading}>{title}</h2><div className="output-dialog-actions">{url?<><a href={url} target="_blank" rel="noopener noreferrer" onClick={onOpenBrowser}>Open in browser ↗</a><button type="button" onClick={fullscreen}>Fullscreen</button></>:null}<button type="button" autoFocus onClick={onClose}>Close preview</button></div></header>
   {hint?<p className="output-dialog-hint">{hint}</p>:null}
   <div ref={content} className="output-dialog-content" aria-busy={loading}>
    {loading?<p role="status">Opening saved output…</p>:null}
    {error?<div role="alert" className="error"><p>{error}</p>{onRetry?<button type="button" disabled={loading} onClick={onRetry}>Try again</button>:null}</div>:null}
    {fullscreenError?<p role="alert" className="error">{fullscreenError}</p>:null}
    {children??(url&&frameReady?<iframe title={title} src={url} sandbox={scripts?'allow-scripts allow-pointer-lock':''} allow="fullscreen"/>:null)}
   </div>
  </section>
 </dialog>,document.body);
}

export function SavedOutputActions({title,url,file,text}:{title:string;url:string;file:string;text:string|null}){
 const [open,setOpen]=useState(false),image=/\.(png|jpe?g)$/i.test(file),report=/\.md$/i.test(file);
 return <div className="saved-output-actions"><button type="button" onClick={()=>setOpen(true)}>Open output</button><a href={url} target="_blank" rel="noopener noreferrer">Open in browser ↗</a>{open?<OutputDialog title={`${title} · ${file}`} url={url} onClose={()=>setOpen(false)} hint="Saved output. Close this window to return to the dashboard.">{image?<img src={url} alt={file}/>:report?undefined:<pre>{text===null?'Loading file…':text||'This file is empty.'}</pre>}</OutputDialog>:null}</div>;
}
