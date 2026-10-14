import type {ModelInfo,Run} from './types';

export const taskStyles:Record<string,{label:string;color:string}>={
 data_analysis:{label:'Data analysis',color:'#007aff'},
 racing_game:{label:'Racing game',color:'#8b44cc'},
 detective:{label:'Detective',color:'#b86300'},
};
export function taskLabel(row:Pick<Run,'task'|'sensory_track'>){return row.sensory_track==='text_only_detective'?'Detective (text only)':taskStyles[row.task]?.label??row.task;}
const stableRoster=['gemma4:12b-it-q4_K_M','gemma4:26b-a4b-it-q4_K_M','glm-4.7-flash:q4_K_M','laguna-xs.2:q4_K_M','nemotron-3-nano:30b-a3b-q4_K_M','nemotron3:33b-q4_K_M','qwen3.5:27b-q4_K_M','qwen3.5:9b-q4_K_M','qwen3.6:35b-a3b-q4_K_M','gpt-oss:20b','qwen3-coder-next:q4_K_M','qwen3-next:80b-a3b-thinking-q4_K_M','qwen3-vl:30b-a3b-instruct'];
const patterns=[
 {label:'Solid',symbol:'none',rotation:0,x:[1,0],y:[1,0],size:1},
 {label:'Diagonal stripes',symbol:'rect',rotation:Math.PI/4,x:[1,0],y:[3,8],size:1},
 {label:'Horizontal stripes',symbol:'rect',rotation:0,x:[1,0],y:[3,8],size:1},
 {label:'Vertical stripes',symbol:'rect',rotation:Math.PI/2,x:[1,0],y:[3,8],size:1},
 {label:'Large circles',symbol:'circle',rotation:0,x:[7,6],y:[7,6],size:1},
 {label:'Triangles',symbol:'triangle',rotation:0,x:[8,6],y:[8,6],size:1},
 {label:'Diamonds',symbol:'diamond',rotation:0,x:[8,6],y:[9,5],size:1},
 {label:'Crosses',symbol:'path://M3,0H6V3H9V6H6V9H3V6H0V3H3Z',rotation:0,x:[9,6],y:[9,6],size:1},
 {label:'Stars',symbol:'path://M5,0L6.5,3.3L10,3.6L7.3,6L8.1,9.6L5,7.8L1.9,9.6L2.7,6L0,3.6L3.5,3.3Z',rotation:0,x:[10,6],y:[10,6],size:1},
 {label:'Hollow squares',symbol:'path://M0,0H10V9.6H0ZM2,2V7.6H8V2Z',rotation:0,x:[10,7],y:[10,7],size:1},
 {label:'X marks',symbol:'path://M0,2L2,0L5,3L8,0L10,2L7,5L10,8L8,10L5,7L2,10L0,8L3,5Z',rotation:0,x:[10,7],y:[10,7],size:1},
 {label:'Hexagons',symbol:'path://M2.5,0H7.5L10,4.8L7.5,9.6H2.5L0,4.8Z',rotation:0,x:[10,7],y:[10,7],size:1},
 {label:'Checkerboard',symbol:'path://M0,0H5V4.8H0ZM5,4.8H10V9.6H5Z',rotation:0,x:[10,5],y:[10,5],size:1},
];
export function modelStyles(models:ModelInfo[]){
 // Use the full discovered roster, never the filtered rows, so selections cannot reassign fills.
 return Object.fromEntries([...new Set(models.map(m=>m.name))].sort().map((name,offset)=>{
  const index=stableRoster.includes(name)?stableRoster.indexOf(name):stableRoster.length+offset;
  const pattern=patterns[index]??{...patterns[1],label:`Fine stripes ${index-8}`,rotation:(index+1)*Math.PI/18,y:[2,6+index]};
  const width=pattern.x[1]===0?8:pattern.x[0]+pattern.x[1],height=pattern.y[0]+pattern.y[1];
  const symbolWidth=(pattern.x[1]===0?width:pattern.x[0])*pattern.size,symbolHeight=pattern.y[0]*pattern.size;
  const x=((pattern.x[1]===0?width:pattern.x[0])-symbolWidth)/2,y=(pattern.y[0]-symbolHeight)/2;
  const shape=pattern.symbol.startsWith('path://')?`<path d="${pattern.symbol.slice(7)}" transform="translate(${x} ${y}) scale(${symbolWidth/(pattern.label==='Crosses'?9:10)} ${symbolHeight/(pattern.label==='Crosses'?9:9.6)})"/>`:pattern.symbol==='circle'?`<ellipse cx="${x+symbolWidth/2}" cy="${y+symbolHeight/2}" rx="${symbolWidth/2}" ry="${symbolHeight/2}"/>`:pattern.symbol==='triangle'?`<polygon points="${x+symbolWidth/2},${y} ${x+symbolWidth},${y+symbolHeight} ${x},${y+symbolHeight}"/>`:pattern.symbol==='diamond'?`<polygon points="${x+symbolWidth/2},${y} ${x+symbolWidth},${y+symbolHeight/2} ${x+symbolWidth/2},${y+symbolHeight} ${x},${y+symbolHeight/2}"/>`:`<rect x="${x}" y="${y}" width="${symbolWidth}" height="${symbolHeight}"/>`;
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="44"><defs><pattern id="p" patternUnits="userSpaceOnUse" width="${width}" height="${height}" patternTransform="rotate(${pattern.rotation*180/Math.PI})"><g fill="white" fill-opacity=".85">${shape}</g></pattern></defs><rect width="64" height="44" fill="url(#p)"/></svg>`;
  return [name,{code:`M${index+1}`,label:pattern.label,css:pattern.symbol==='none'?'none':`url("data:image/svg+xml,${encodeURIComponent(svg)}")`,
   decal:pattern.symbol==='none'?undefined:{symbol:pattern.symbol,symbolSize:pattern.size,rotation:pattern.rotation,dashArrayX:pattern.x,dashArrayY:pattern.y,color:'rgba(255,255,255,0.85)',backgroundColor:'transparent'}}];
 }));
}
export type ModelStyles=ReturnType<typeof modelStyles>;
export function itemStyle(row:Run,models:ModelStyles){return {color:taskStyles[row.task]?.color??'#65758b',decal:models[row.model.name]?.decal,borderRadius:[4,4,0,0]};}
