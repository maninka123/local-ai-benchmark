import type {ModelInfo} from './types';
const paths={text:<><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v5h4M10 12h5M10 16h5"/></>,image:<><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="9" r="1.5"/><path d="m4 18 5-5 4 4 3-4 5 5"/></>,video:<><rect x="3" y="5" width="14" height="14" rx="3"/><path d="m17 10 4-3v10l-4-3zM9 9l4 3-4 3z"/></>};
export default function InputIcons({model}:{model:ModelInfo}){
 const inputs=['text',...(model.vision?['image']:[]),...(model.input_video?.supported||model.capabilities?.includes('video')?['video']:[])] as (keyof typeof paths)[];
 return <span className="input-icons" aria-label="Supported model inputs">{inputs.map(kind=>{const label=kind==='text'?'Text input':kind==='image'?'Image input':model.input_video?.note??'Video input';return <span className={`input-icon input-${kind}`} key={kind} role="img" aria-label={label} title={label}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[kind]}</svg></span>;})}</span>;
}
