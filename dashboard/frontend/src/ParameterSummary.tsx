import type {ModelInfo} from './types';
export const billions=(value:number|null|undefined)=>typeof value==='number'?`${(value/1e9).toFixed(1)}B`:'Not reported';
export function estimatedActiveGB(model:ModelInfo){
 const p=model.parameter_comparison?.calculated;
 const total=(p?.total??0)+(p?.auxiliary_parameters??0);
 return typeof p?.active==='number'&&total>0&&model.size>0?model.size/1e9*p.active/total:null;
}
export function ModelSize({model}:{model:ModelInfo}){
 const comparison=model.parameter_comparison;
 return <small className="model-size"><span>Model parameters: <b>{model.parameters}</b></span><span>Active parameters: <b>{billions(model.active_parameters??comparison?.reported.active)}</b>{!model.active_parameters&&comparison?.reported.active?' · reported':null}</span><span title="Installed model-file size, separate from runtime RAM and VRAM">Model size: <b>{typeof model.size==='number'?`${(model.size/1e9).toFixed(1)} GB`:'Unavailable'}</b></span></small>;
}
export default function ParameterSummary({model}:{model:ModelInfo}){
 const p=model.parameter_comparison;
 const activeGB=estimatedActiveGB(model);
 const experts=p?.calculated.method?.match(/\((\d+) of (\d+) experts per MoE layer\)/);
 const rule=experts?`GGUF weights minus inactive experts (${experts[1]} of ${experts[2]} used per MoE layer). Shared and other language weights included; encoders excluded.`:p?.calculated.method?.startsWith('Dense model:')?'Dense model: all language weights counted as active. Encoders excluded.':p?.calculated.method??'Calculation unavailable.';
 return <div className="parameter-summary"><b>Calculated active: {typeof p?.calculated.active==='number'?billions(p.calculated.active):'Unavailable'}</b><span>Share of total: {typeof p?.calculated.percent==='number'?`${p.calculated.percent.toFixed(1)}%`:'Unavailable'}</span><span className="active-storage">Estimated active size: <b>{activeGB===null?'Unavailable':`${activeGB.toFixed(1)} GB`}</b></span><details><summary>Method</summary><p>{rule}</p><p>Share = active ÷ {billions(p?.calculated.total)} language parameters × 100. B = billion.</p><p>Active GB = model-file GB × active ÷ all counted parameters, including encoders. Decimal GB; assumes equal average bytes per parameter. Quantization and file overhead affect accuracy.</p><p>Structural estimates; runtime activations and memory use were not measured by this calculation.</p>{p?.calculated.auxiliary_parameters?<p>Separate encoder/projector weights: {billions(p.calculated.auxiliary_parameters)}.</p>:null}{p?.reported.source?<a href={p.reported.source} target="_blank" rel="noreferrer">Publisher reference</a>:null}</details></div>;
}
