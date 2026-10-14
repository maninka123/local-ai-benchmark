import {useEffect,useRef,useState} from 'react';
import OutputDialog from './OutputDialog';

export type GameEvidence={build_success?:boolean;browser?:{build?:boolean;errors?:string[];checks?:{canvas?:boolean}}};
function gameEvidence(value:unknown):GameEvidence{return value&&typeof value==='object'?value as GameEvidence:{};}
export function hasGameBuild(value:unknown){const evidence=gameEvidence(value);return evidence.build_success===true||evidence.browser?.build===true;}
export function savedGameIssue(value:unknown){
 const evidence=gameEvidence(value),errors=Array.isArray(evidence.browser?.errors)?evidence.browser.errors.filter(e=>typeof e==='string'):[];
 if(errors.length)return 'Saved game runtime error: '+errors.slice(0,2).join(' · ');
 if(evidence?.browser?.checks?.canvas===false)return 'The saved page opens, but no game canvas appeared during evaluation. This model output is incomplete.';
 return '';
}

export default function GamePreview({endpoint,available,title,reason,issue='',modelName}:{endpoint:string;available:boolean;title:string;reason?:string;issue?:string;modelName?:string}){
 const [session]=useState(()=>crypto.randomUUID().replaceAll('-',''));
 const viewerEndpoint=`${endpoint}${endpoint.includes('?')?'&':'?'}session_id=${session}`;
 const [url,setUrl]=useState(''),[visible,setVisible]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(''),[detached,setDetached]=useState(false);
 const generation=useRef(0),active=useRef(false),external=useRef(false),pending=useRef(false);
 const stop=()=>fetch(viewerEndpoint,{method:'DELETE'}).catch(()=>undefined);
 useEffect(()=>{const token=++generation.current;return()=>{if(generation.current===token)generation.current++;if(active.current&&!external.current){active.current=false;void fetch(viewerEndpoint,{method:'DELETE'}).catch(()=>undefined);}};},[viewerEndpoint]);
 async function open(){if(loading)return;setVisible(true);if(url)return;const token=generation.current;setError('');setLoading(true);pending.current=true;active.current=true;
  try{const response=await fetch(viewerEndpoint,{method:'POST'}),value=await response.json();if(!response.ok)throw Error(value.detail||'Game preview unavailable');if(token!==generation.current){await stop();return;}setUrl(value.url);}
  catch(e){if(token===generation.current)setError((e as Error).message);}
  finally{pending.current=false;setLoading(false);}
 }
 function close(){setVisible(false);if(external.current)return;generation.current++;setUrl('');setError('');active.current=false;setLoading(true);void stop().finally(()=>{if(!pending.current)setLoading(false);});}
 function detach(){external.current=true;setDetached(true);}
 function stopServer(){external.current=false;setDetached(false);close();}
 return <section className="game-preview" aria-label={title}>
  <div className="game-preview-toolbar"><h3>{title}</h3><button type="button" disabled={!available||loading} onClick={open}>{loading?'Opening game…':'Open game preview'}</button>{url?<a href={url} target="_blank" rel="noopener noreferrer" onClick={detach}>Open in browser ↗</a>:null}{url&&detached?<button type="button" onClick={stopServer}>Stop preview server</button>:null}</div>
  <p className="scope-hint">{available?'Opens the saved evaluated build in a popup. Click inside to use the keyboard. This output may still be incomplete; check its completion review.':reason||'This game did not produce a successful build. Its source files and saved screenshots are available above.'}</p>
  {issue?<p className="saved-game-issue" role="note">{issue}</p>:null}
  {visible?<OutputDialog title={modelName?`${modelName} · ${title}`:title} url={url||undefined} scripts loading={loading} error={error} onRetry={open} onClose={close} onOpenBrowser={detach} hint={issue||'Click inside the game to use its keyboard controls. Open in browser keeps the game available after closing this popup.'}/>:null}
 </section>;
}
