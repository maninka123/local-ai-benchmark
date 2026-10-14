import {lazy,Suspense,useEffect,useMemo,useState} from 'react';
import type {Run,Summary} from './types';
import Chart from './Chart';
import ProgressPanel from './ProgressPanel';
import FigureLegend from './FigureLegend';
import ComparisonTable from './ComparisonTable';
import OverviewComparison from './OverviewComparison';
import BenchmarkGuide from './BenchmarkGuide';
import {taskStyles,modelStyles} from './chartStyles';
import {modelLabel} from './modelNames';
import {buildFigureCharts,figureGroups} from './figureCharts';
const RunDetail=lazy(()=>import('./RunDetail'));
const ModelOutputs=lazy(()=>import('./ModelOutputs'));
const TaskBoard=lazy(()=>import('./TaskBoard'));
const JudgedResults=lazy(()=>import('./JudgedResults'));
const ReferenceResults=lazy(()=>import('./ReferenceResults'));
const fmt=(v:unknown,d=1)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(d):'—';

const resultViews=[
 {value:'campaign',label:'Initial results',hint:'Saved initial benchmark outputs and scores. Further prompts leave these results preserved.'},
 {value:'updates',label:'After updates',hint:'Latest further work for each initial result. Scores appear after re-evaluation; time includes initial work plus all updates and evaluations.'},
];

export default function App(){
 const [summary,setSummary]=useState<Summary|null>(null),[error,setError]=useState(''),[model,setModel]=useState(''),[task,setTask]=useState(''),[quant,setQuant]=useState(''),[arch,setArch]=useState(''),[vision,setVision]=useState(''),[residency,setResidency]=useState(''),[date,setDate]=useState(''),[sort,setSort]=useState('start'),[direction,setDirection]=useState(-1),[selected,setSelected]=useState('');
 const [protocol,setProtocol]=useState('campaign'),[includeHistory,setIncludeHistory]=useState(false),[outputRunId,setOutputRunId]=useState(()=>new URLSearchParams(window.location.search).get('run_id')??'');
 const [tab,setTab]=useState<'comparison'|'outputs'|'tasks'|'references'|'reviews'|'guide'>(()=>new URLSearchParams(window.location.search).get('tab')==='reviews'?'reviews':new URLSearchParams(window.location.search).get('tab')==='references'?'references':new URLSearchParams(window.location.search).has('run_id')?'outputs':'guide');
 const [figureMode,setFigureMode]=useState<'all'|'model'|'task'>('task'),[figureModel,setFigureModel]=useState(''),[figureTask,setFigureTask]=useState('racing_game');
 useEffect(()=>{const controller=new AbortController();async function update(){try{const response=await fetch('/api/summary',{signal:controller.signal});if(!response.ok)throw Error('Dashboard data unavailable');setSummary(await response.json());setError('');}catch(e){if((e as Error).name!=='AbortError')setError(String(e));}}update();const timer=setInterval(update,10000);return()=>{controller.abort();clearInterval(timer);};},[]);
 const cohortRows=useMemo(()=>{
 const campaignIds=new Set(summary?.campaign?.run_ids??(summary?.runs??[]).filter(r=>r.protocol_hash===summary?.runs.at(-1)?.protocol_hash).map(r=>r.run_id));
 const latest=new Map<string,NonNullable<Summary['modifications']>[number]>();
 for(const revision of summary?.modifications??[]){const previous=latest.get(revision.base_run_id);if(!previous||revision.workspace_mode||!previous.workspace_mode&&revision.created>previous.created)latest.set(revision.base_run_id,revision);}
 return (summary?.runs??[]).filter(r=>includeHistory||campaignIds.has(r.run_id)).flatMap(r=>{
  if(protocol!=='updates')return [r];const revision=latest.get(r.run_id);if(!revision||revision.workspace_mode&&!revision.prompts?.length)return [];
  const evaluation=revision.evaluations.at(-1),current=evaluation&&(!revision.workspace_mode||evaluation.update_id===revision.current_update_id);
  const related=(summary?.modifications??[]).filter(m=>m.base_run_id===r.run_id),extra=related.reduce((sum,m)=>sum+(m.extra_seconds??m.generation_seconds),0);
  const scores=current&&evaluation.scores?evaluation.scores:{...r.scores,verified_points:0,pending_points:100,quality_score:null,complete:false,categories:Object.fromEntries(Object.keys(r.scores.rubric).map(k=>[k,null])),evidence:{},limitations:['Further output awaits re-evaluation.']};
  const performance={generation_tps:null,prompt_tps:null,ttft:{median:null},peak_vram_bytes:null,peak_ram_bytes:null,tool_calls:0,tool_failures:0,inference_calls:0,tool_categories:{},...revision.performance};
  return [{...r,status:current&&evaluation.scores?'evaluated':revision.status,scores,performance,task_seconds:r.task_seconds+extra,start:revision.prompts?.at(-1)?.created??revision.created,after_updates:{status:revision.status,scored:!!current&&!!evaluation?.scores,initial_seconds:r.task_seconds,extra_seconds:extra},config:{...(r.config as object),benchmark:{...((r.config as {benchmark:object}).benchmark),task_timeout_seconds:3600}}}];
 }).filter(r=>(!quant||r.model.quantization===quant)&&(!arch||r.model.architecture===arch)&&(!vision||String(r.model.vision)===vision)&&(!date||r.start.slice(0,10)===date)&&(!residency||(r.residency&&((r.residency.size_vram/r.residency.size>.98?'gpu':'hybrid')===residency))));
 },[summary,quant,arch,vision,date,residency,protocol,includeHistory]);
 const rows=useMemo(()=>{const filtered=cohortRows.filter(r=>(!model||r.model.name===model)&&(!task||r.task===task));
 const val=(r:Run):string|number=>sort==='model'?r.model.name:sort==='parameters'?r.model.parameter_comparison?.calculated.percent??-1:sort==='quality'?r.scores.verified_points:sort==='speed'?r.performance.generation_tps??-1:sort==='time'?r.task_seconds:sort==='complete'?Number(r.scores.complete):r.start;
 return [...filtered].sort((a,b)=>{const av=val(a),bv=val(b);return (av>bv?1:av<bv?-1:0)*direction;});},[cohortRows,model,task,sort,direction]);
 const chosenFigureModel=figureModel||summary?.models[0]?.name||'';
 const figureRows=useMemo(()=>cohortRows.filter(r=>figureMode==='all'||(figureMode==='model'?r.model.name===chosenFigureModel:r.task===figureTask)),[cohortRows,figureMode,chosenFigureModel,figureTask]);
 const fills=useMemo(()=>modelStyles(summary?.models??[]),[summary?.models]);
 const charts=useMemo(()=>buildFigureCharts(figureRows,figureMode,fills),[figureRows,figureMode,fills]);
 function order(key:string){if(sort===key)setDirection(d=>-d);else{setSort(key);setDirection(-1);}}
 const select=(label:string,value:string,set:(v:string)=>void,options:string[])=> <label>{label}<select value={value} onChange={e=>set(e.target.value)}><option value="">All</option>{options.map(o=><option key={o}>{o}</option>)}</select></label>;
 const unique=(get:(r:Run)=>string)=>[...new Set((summary?.runs??[]).map(get))].sort();
 if(!summary)return <main><h1>Local LLM Lab</h1><p role={error?'alert':'status'}>{error||'Loading results…'}</p></main>;
 const fast=[...rows].filter(r=>r.performance.generation_tps!==null).sort((a,b)=>b.performance.generation_tps!-a.performance.generation_tps!)[0];
 const scored=rows.filter(r=>r.scores.quality_score!==null&&r.scores.quality_score>0).sort((a,b)=>b.scores.quality_score!-a.scores.quality_score!)[0];
 const originalSeconds=rows.reduce((sum,r)=>sum+(r.after_updates?.initial_seconds??r.task_seconds),0);
 const includedIds=new Set(rows.map(r=>r.run_id));
 const extraSeconds=(summary.modifications??[]).filter(r=>includedIds.has(r.base_run_id)).reduce((sum,r)=>sum+(r.extra_seconds??r.generation_seconds),0);
 return <main><header><div><p className="eyebrow">LOCAL CAPABILITY BENCHMARK / PILOT</p><h1>{tab==='references'?<>Astra's answers.<br/><span>Explore the results.</span></>:<>Your models.<br/><span>Measured on your PC.</span></>}</h1><p className="intro">{tab==='references'?'Original benchmark tasks, completed as separate frontier references. Play the game, explore the analysis, and inspect the evidence.':<>Intelligence, coding, visual reasoning and computational cost — inspect the output files behind each result.</>}</p></div><div className="hardware">RTX 4080 · 16 GB VRAM<br/>i9-13900K · 64 GB RAM<br/><span className="live">{summary.running?'Benchmark running':summary.modifications?.some(r=>['queued','launching','running','queued_score','reevaluating'].includes(r.status))?'Model improvement running':'Saved results'} · updates every 10s</span></div></header>
 {error?<p className="error" role="alert">{error}</p>:null}
 <nav className="view-buttons main-tabs" aria-label="Dashboard sections"><button type="button" aria-pressed={tab==='guide'} onClick={()=>setTab('guide')}>Start here</button><button type="button" aria-pressed={tab==='comparison'} onClick={()=>setTab('comparison')}>Comparison</button><button type="button" aria-pressed={tab==='outputs'} onClick={()=>{setOutputRunId('');setTab('outputs');}}>Model outputs</button><button type="button" aria-pressed={tab==='tasks'} onClick={()=>setTab('tasks')}>Task progress</button><button type="button" aria-pressed={tab==='reviews'} onClick={()=>setTab('reviews')}>Review scores</button><span className="reference-tab"><span className="tab-divider" aria-hidden="true">|</span><button type="button" aria-pressed={tab==='references'} onClick={()=>setTab('references')}>Astra references</button></span></nav>
 {tab==='guide'?<BenchmarkGuide summary={summary} onNavigate={setTab}/>:tab==='reviews'?<Suspense fallback={<p>Loading reviews...</p>}><JudgedResults onOpen={id=>{setOutputRunId(id);setTab('outputs');}}/></Suspense>:tab==='references'?<Suspense fallback={<p>Loading Astra references…</p>}><ReferenceResults/></Suspense>:tab==='tasks'?<Suspense fallback={<p>Loading task progress…</p>}><TaskBoard summary={summary} onOpen={id=>{setOutputRunId(id);setTab('outputs');}}/></Suspense>:tab==='outputs'?<Suspense fallback={<p>Loading model outputs…</p>}><ModelOutputs summary={summary} initialRunId={outputRunId}/></Suspense>:<>
 <ProgressPanel progress={summary.progress}/>
 {summary.campaign?<p className="campaign-note">{summary.campaign.note}</p>:null}
 <section className="cards"><article><small>Installed models</small><strong>{summary.models.length}</strong></article><article><small>Evaluated attempts</small><strong>{rows.filter(r=>r.status==='evaluated').length}</strong></article><article><small>Failed attempts</small><strong>{rows.filter(r=>r.status==='failed').length}</strong></article><article><small>Automatic checks passed</small><strong>{rows.filter(r=>r.scores.complete).length}<em> / {rows.length}</em></strong></article><article><small>Original task time</small><strong>{fmt(originalSeconds/60)}<em> min</em></strong></article><article><small>Extra revision time</small><strong>{fmt(extraSeconds/60)}<em> min</em></strong></article><article><small>Combined time</small><strong>{fmt((originalSeconds+extraSeconds)/60)}<em> min</em></strong></article></section>
 <p className="notice">Output review scores are saved separately from automatic checks and use your attempt-based bands. Select Review scores for the full rubric and completion reasons. Automatic scores may still have criteria awaiting human review. Visual and written-only Detective inputs remain distinct.</p>
 <p className="leaders">Fastest observed generation: <b>{fast?modelLabel(fast.model.name):'Pending'}</b> · Automatic score leader: <b>{scored?modelLabel(scored.model.name):'Pending review'}</b></p>
 <section className="filters" aria-label="Result filters">
  <fieldset className="result-scope"><legend>Show results</legend><div className="view-buttons">{resultViews.map(view=><button key={view.value} type="button" aria-pressed={protocol===view.value} onClick={()=>setProtocol(view.value)}>{view.label}</button>)}</div><p className="scope-hint">{resultViews.find(view=>view.value===protocol)?.hint}</p></fieldset><details className="saved-result-choice"><summary>Earlier test history</summary><label className="inline-checkbox"><input type="checkbox" checked={includeHistory} onChange={e=>setIncludeHistory(e.target.checked)}/>Include earlier tests and setup runs</label></details>
  <details className="advanced-filters"><summary>Advanced filters{[quant,arch,vision,residency,date].filter(Boolean).length?` · ${[quant,arch,vision,residency,date].filter(Boolean).length} active`:''}</summary><div className="advanced-filter-controls">
   {select('Quantization',quant,setQuant,unique(r=>r.model.quantization))}{select('Architecture',arch,setArch,unique(r=>r.model.architecture))}{select('Vision',vision,setVision,['true','false'])}{select('Residency',residency,setResidency,['gpu','hybrid'])}<label>UTC date<input type="date" value={date} onChange={e=>setDate(e.target.value)}/></label><button type="button" onClick={()=>{setModel('');setTask('');setQuant('');setArch('');setVision('');setResidency('');setDate('');}}>Clear filters</button>
  </div></details>
 </section>
 <OverviewComparison rows={cohortRows} summary={summary} updated={protocol==='updates'} onOpen={id=>{setOutputRunId(id);setTab('outputs');}}/>
 <section className="figure-controls" aria-label="Figure selection"><h2>Figures</h2><div className="figure-toolbar"><fieldset className="figure-scope"><legend>Show figures</legend><div className="view-buttons" aria-label="Choose figures"><button type="button" aria-pressed={figureMode==='all'} onClick={()=>setFigureMode('all')}>All results</button><button type="button" aria-pressed={figureMode==='model'} onClick={()=>setFigureMode('model')}>One model</button><button type="button" aria-pressed={figureMode==='task'} onClick={()=>setFigureMode('task')}>One task</button></div></fieldset>
  {figureMode==='model'?<label>Model for figures<select value={chosenFigureModel} onChange={e=>setFigureModel(e.target.value)}>{summary.models.map(m=><option key={m.name} value={m.name} title={m.name}>{modelLabel(m.name)}</option>)}</select></label>:null}
  {figureMode==='task'?<label>Task for figures<select value={figureTask} onChange={e=>setFigureTask(e.target.value)}>{Object.entries(taskStyles).map(([key,style])=><option key={key} value={key}>{style.label}</option>)}</select></label>:null}
  </div>
  <p className="scope-hint">{figureMode==='model'?'All available tasks for this model.':figureMode==='task'?'Every model with results for this task.':'All models and available tasks.'} Applies to all 11 plots · {figureRows.length} saved attempts. Detective cases appear as one average per model, with equal weight per case; unavailable values are omitted. Text-only results stay separate. Result set and advanced filters apply here. Table filters below are separate.</p>
 </section>
 <div className="figure-context"><div><h3>{figureMode==='task'?taskStyles[figureTask]?.label:figureMode==='model'?modelLabel(chosenFigureModel):'All results'}</h3><p>{protocol==='updates'?'After updates':'Initial results'} · {figureRows.length} attempts · {new Set(figureRows.map(r=>r.model.name)).size} models</p></div><span>11 figures</span></div>
 <FigureLegend tasks={[...new Set(figureRows.map(r=>r.task))]} models={Object.fromEntries(Object.entries(fills).filter(([name])=>figureRows.some(r=>r.model.name===name)))}/>
 {figureGroups.map(group=><section className="figure-group" key={group} aria-label={group}><div className="section-heading"><h2>{group}</h2></div><div className="chart-grid">{charts.filter(c=>c.group===group).map(c=><Chart key={c.title} {...c}/>)}</div></section>)}
 <section className="attempt-section" aria-label="Attempt details"><div className="section-heading"><h2>Attempt details</h2><p>Inspect individual results, scores and saved outputs.</p></div><div className="comparison-filters" aria-label="Table filters">
  <label>Model<select value={model} onChange={e=>setModel(e.target.value)}><option value="">All models</option>{summary.models.map(m=><option key={m.name} value={m.name} title={m.name}>{modelLabel(m.name)}</option>)}</select></label><label>Task<select value={task} onChange={e=>setTask(e.target.value)}><option value="">All tasks</option>{Object.entries(taskStyles).map(([key,style])=><option key={key} value={key}>{style.label}</option>)}</select></label>{model||task?<button type="button" onClick={()=>{setModel('');setTask('');}}>Clear Model / Task</button>:null}
 </div>
 <ComparisonTable rows={rows} sort={sort} direction={direction} onSort={order} onOpen={id=>{if(protocol==='updates'){setOutputRunId(id);setTab('outputs');}else setSelected(id);}}/>
 </section>
 <details><summary>Environment, isolation and setup validation</summary><pre>{JSON.stringify({environment:summary.environment,validation:summary.setup,models:summary.models},null,2)}</pre></details>
 </>}
 <footer>Local benchmark: exact API token statistics · one model at a time · preserved attempts · frontier references in their own tab · DeepSeek-OCR excluded</footer>
 {selected?<div className="modal"><Suspense fallback={<section className="detail">Loading attempt viewer…</section>}><RunDetail key={selected} id={selected} onClose={()=>setSelected('')}/></Suspense></div>:null}</main>;
}
