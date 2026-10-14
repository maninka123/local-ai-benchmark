import {useEffect,useRef,useState} from 'react';
import type {CompactBar} from './figureCharts';
import * as echarts from 'echarts/core';
import {BarChart,LineChart,ScatterChart} from 'echarts/charts';
import {GridComponent,TooltipComponent,LegendComponent,TitleComponent,DataZoomComponent,AriaComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import {LabelLayout} from 'echarts/features';
echarts.use([BarChart,LineChart,ScatterChart,GridComponent,TooltipComponent,LegendComponent,TitleComponent,DataZoomComponent,AriaComponent,CanvasRenderer,LabelLayout]);
export default function Chart({title,subtitle,option,height=390,emptyMessage,bars,barMax=1,unit}:{title:string;subtitle?:string;option:echarts.EChartsCoreOption;height?:number;emptyMessage?:string;bars?:CompactBar[];barMax?:number;unit?:string}){
 const root=useRef<HTMLDivElement>(null);
 const section=useRef<HTMLElement>(null);
 const [compact,setCompact]=useState(false);
 useEffect(()=>{
  const element=section.current;if(!element)return;
  const resize=new ResizeObserver(()=>setCompact(element.clientWidth<600));
  setCompact(element.clientWidth<600);resize.observe(element);
  return()=>resize.disconnect();
 },[]);
 useEffect(()=>{
  if(emptyMessage||(compact&&bars)||!root.current)return;
  const element=root.current;
  const decimal=(v:unknown)=>typeof v==='number'?(Number.isInteger(v)?String(v):v.toFixed(1)):String(v??'');
  const axes=(axis:unknown)=>{
   const format=(a:Record<string,unknown>)=>({...a,axisLabel:{...(a.axisLabel as object??{}),...(a.type==='value'||a.type==='log'?{formatter:decimal}:a.type==='category'?{width:Math.min(215,Math.max(120,element.clientWidth*.32))}:{})},splitLine:{lineStyle:{color:'#e9edf2',type:'dashed'},...(a.splitLine as object??{})}});
   return Array.isArray(axis)?axis.map(format):axis?format(axis as Record<string,unknown>):axis;
  };
  const c=echarts.init(element);
  const grid=()=>bars?{...(option.grid as object),left:Math.min(215,Math.max(120,element.clientWidth*.32))+20}:option.grid;
  c.setOption({color:['#007aff','#34a853','#af52de'],textStyle:{fontFamily:'Segoe UI, system-ui, sans-serif',fontSize:16,color:'#374151'},...option,grid:grid(),xAxis:axes(option.xAxis),yAxis:axes(option.yAxis),tooltip:{backgroundColor:'#fff',borderColor:'#dce0e6',textStyle:{fontSize:16,color:'#374151'},...(option.tooltip as object??{}),valueFormatter:decimal},aria:{enabled:true,label:{description:`${title}. ${subtitle??''}`}},backgroundColor:'transparent',animation:!matchMedia('(prefers-reduced-motion: reduce)').matches});
  const resize=new ResizeObserver(()=>{c.resize();c.setOption({grid:grid(),xAxis:axes(option.xAxis),yAxis:axes(option.yAxis)});});
  resize.observe(element);
  return()=>{resize.disconnect();c.dispose();};
 },[option,emptyMessage,title,subtitle,compact,bars]);
 const number=(value:number)=>Number.isInteger(value)?String(value):value.toFixed(1);
 return <section className="chart" ref={section}>
  <h3>{title}</h3>{subtitle?<p className="chart-subtitle">{subtitle}</p>:null}
  {emptyMessage?<div key="empty" className="chart-empty" role="img" aria-label={`${title}. ${emptyMessage}`} style={{minHeight:compact?240:height}}><p>{emptyMessage}</p></div>
   :compact&&bars?<div key="compact" className="compact-bars" role="img" aria-label={`${title}. ${bars.map(bar=>`${bar.label.replaceAll('\n',', ')}: ${bar.value===null?'not recorded':number(bar.value)+' '+unit}`).join('; ')}`} tabIndex={bars.length>8?0:undefined}>
    {bars.map(bar=><div className="compact-bar-row" key={bar.id} title={bar.detail}>
     <div className="compact-bar-label"><span>{bar.label.replaceAll('\n',' · ')}</span><strong>{bar.value===null?'—':number(bar.value)}</strong></div>
     <div className="compact-bar-track"><div style={{width:`${bar.value===null?0:Math.min(100,100*bar.value/barMax)}%`,backgroundColor:bar.color,backgroundImage:bar.pattern,backgroundSize:'64px 44px'}}/></div>
    </div>)}
   </div>
   :<div key="canvas" ref={root} role="img" aria-label={title} style={{height}}/>}
 </section>;
}
