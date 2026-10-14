import {taskStyles} from './chartStyles';
import type {ModelStyles} from './chartStyles';
import {modelLabel} from './modelNames';
export default function FigureLegend({models,tasks}:{models:ModelStyles;tasks:string[]}){
 return <details className="figure-legend"><summary>Chart key · task colours and model patterns</summary>
  <div className="task-legend">{Object.entries(taskStyles).filter(([task])=>tasks.includes(task)).map(([task,style])=><span key={task}><i aria-hidden="true" style={{backgroundColor:style.color}}/>{style.label}</span>)}</div>
  <p className="scope-hint">Names use family and variant, followed by total parameters when available. Exact model IDs and quantization remain available in the attempt details.</p>{tasks.includes('detective')?<p className="scope-hint">Detective (text only) uses written evidence and a separate rubric from visual tests.</p>:null}<div className="model-legend">{Object.entries(models).map(([name,style])=><span key={name}><i aria-hidden="true" style={{backgroundColor:'#65758b',backgroundImage:style.css,backgroundSize:'100% 100%'}}/><span><b title={name}>{modelLabel(name)}</b><small>{style.label}</small></span></span>)}</div>
 </details>;
}
