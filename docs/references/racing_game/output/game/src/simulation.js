export const TAU=Math.PI*2;
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const angleDelta=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
export const CARS=[
 {id:'comet',name:'Comet GT',tag:'THE ALL-ROUNDER',color:'#f66b42',accent:'#ffe6a3',max:38,accel:13,brake:25,grip:1.70,width:2.0,length:4.5,desc:'Balanced pace. Predictable through every apex.'},
 {id:'spectre',name:'Spectre R',tag:'THE STRAIGHT-LINE SPECIALIST',color:'#b5a3ff',accent:'#30265b',max:44,accel:10,brake:21,grip:1.38,width:2.2,length:4.9,desc:'Long legs, a wide stance and serious top speed.'},
 {id:'swift',name:'Swift RS',tag:'THE CORNER CARVER',color:'#60e2c1',accent:'#163d42',max:34,accel:16,brake:30,grip:2.05,width:1.85,length:3.9,desc:'Light, eager and built for late braking.'}
];
// Rounded rectangle, counterclockwise in world x/z. Four 90-degree bends and four straights.
const pieces=[
 {len:120,x:-60,z:85,dx:1,dz:0},
 {len:Math.PI*20,cx:60,cz:45,r:40,a:Math.PI/2},
 {len:90,x:100,z:45,dx:0,dz:-1},
 {len:Math.PI*20,cx:60,cz:-45,r:40,a:0},
 {len:120,x:60,z:-85,dx:-1,dz:0},
 {len:Math.PI*20,cx:-60,cz:-45,r:40,a:-Math.PI/2},
 {len:90,x:-100,z:-45,dx:0,dz:1},
 {len:Math.PI*20,cx:-60,cz:45,r:40,a:-Math.PI}
];
export const LENGTH=pieces.reduce((s,p)=>s+p.len,0), HALF_WIDTH=10, CHECKPOINTS=16;
export function trackAt(s,lane=0){
 s=((s%LENGTH)+LENGTH)%LENGTH;
 for(const p of pieces){if(s<=p.len){let x,z,dx,dz,curve=0;if(p.r){const a=p.a-s/p.r;x=p.cx+p.r*Math.cos(a);z=p.cz+p.r*Math.sin(a);dx=Math.sin(a);dz=-Math.cos(a);curve=1/p.r;}else{x=p.x+p.dx*s;z=p.z+p.dz*s;dx=p.dx;dz=p.dz;}return {x:x-dz*lane,z:z+dx*lane,dx,dz,heading:Math.atan2(dz,dx),curve};}s-=p.len;}
}
// Exact nearest projection to every straight and arc; no sampled-path teleportation.
export function project(x,z){let best={distance:Infinity},offset=0;for(const p of pieces){let t;if(p.r){let a=Math.atan2(z-p.cz,x-p.cx);let swept=((p.a-a)%TAU+TAU)%TAU;t=clamp(swept,0,Math.PI/2)*p.r;if(swept>Math.PI){t=0;}}else{t=clamp((x-p.x)*p.dx+(z-p.z)*p.dz,0,p.len);}const q=trackAt(offset+t);const d=Math.hypot(x-q.x,z-q.z);if(d<best.distance)best={...q,s:(offset+t)%LENGTH,lateral:(x-q.x)*(-q.dz)+(z-q.z)*q.dx,distance:d};offset+=p.len;}return best;}
export const OBSTACLES=[{s:182,lane:-6,r:1.35},{s:356,lane:6.2,r:1.35},{s:545,lane:-6.5,r:1.35}].map(o=>({...o,...trackAt(o.s,o.lane)}));
export class Race {
 constructor(carIndex=0){this.reset(carIndex);}
 reset(carIndex=this.selected){this.selected=carIndex;this.phase='countdown';this.countdown=3.6;this.time=0;this.events=[];this.finishOrder=[];this.paused=false;this.collisionCounts={barrier:0,vehicle:0,obstacle:0};this.cars=[];for(let i=0;i<6;i++){const spec=CARS[i===0?carIndex:(i+1)%3];const s=35-Math.floor(i/2)*8;const lane=i%2===0?-2.8:2.8;const p=trackAt(s,lane);this.cars.push({id:i,name:i===0?'YOU':['','M. Sato','A. Rivera','J. Quinn','N. Vale','S. Moss'][i],spec,x:p.x,z:p.z,heading:p.heading,speed:0,steer:0,lap:0,nextCheckpoint:1,lastS:s,progress:0,lapStart:0,lapTimes:[],finishTime:null,lane,desiredLane:lane,hit:0,blocked:0,recoveries:0,passed:0,collisions:0});}this.startS=45;}
 get player(){return this.cars[0];}
 checkpointS(index){return (this.startS+index*LENGTH/CHECKPOINTS)%LENGTH;}
 checkpoint(c,oldS,newS){const delta=((newS-oldS+LENGTH*1.5)%LENGTH)-LENGTH/2;if(delta<=0||delta>12)return;const target=this.checkpointS(c.nextCheckpoint%CHECKPOINTS);const distance=((target-oldS)%LENGTH+LENGTH)%LENGTH;if(distance>delta+1e-7)return;c.passed++;c.nextCheckpoint++;if(c.nextCheckpoint>CHECKPOINTS){c.lap++;c.lapTimes.push(this.time-c.lapStart);c.lapStart=this.time;c.nextCheckpoint=1;if(c.lap===3){c.finishTime=this.time;this.finishOrder.push(c.id);this.events.push({type:'finish',car:c.id,time:this.time});}}}
 ranking(){return [...this.cars].sort((a,b)=>{if(a.finishTime!==null&&b.finishTime!==null)return a.finishTime-b.finishTime;if(a.finishTime!==null)return -1;if(b.finishTime!==null)return 1;return b.progress-a.progress;});}
 ai(c,dt){
  const q=project(c.x,c.z);let targetLane=c.lane;let hazard=Infinity;
  for(const other of this.cars){if(other===c)continue;const dx=other.x-c.x,dz=other.z-c.z;const forward=dx*q.dx+dz*q.dz,side=dx*(-q.dz)+dz*q.dx;if(forward>0&&forward<23&&Math.abs(side)<3.5){hazard=Math.min(hazard,forward);targetLane=q.lateral>0?-3.8:3.8;}}
  for(const o of OBSTACLES){const ahead=((o.s-q.s)%LENGTH+LENGTH)%LENGTH;if(ahead<32&&Math.abs(o.lane-q.lateral)<4){targetLane=o.lane>0?-2.6:2.6;hazard=Math.min(hazard,ahead);}}
  c.desiredLane+=(targetLane-c.desiredLane)*Math.min(1,dt*1.4);
  const lookahead=8+Math.abs(c.speed)*.46;const target=trackAt(q.s+lookahead,c.desiredLane);const aim=Math.atan2(target.z-c.z,target.x-c.x);const err=angleDelta(aim,c.heading);
  const ahead=trackAt(q.s+16);let desired=Math.min(c.spec.max*(.76+(c.id%3)*.025),ahead.curve?24+(c.id%3)*.65:34);
  desired*=clamp(1-Math.abs(err)*.38,.38,1);if(hazard<7)desired=Math.min(desired,10);
  c.blocked=(Math.abs(c.speed)<2&&this.time>2)?c.blocked+dt:Math.max(0,c.blocked-dt);
  if(c.blocked>2.5){this.recover(c);return {throttle:1,brake:0,steer:0};}
  return {throttle:c.speed<desired?1:0,brake:c.speed>desired+1?.6:0,steer:clamp(err*2.6,-1,1)};
 }
 recover(c){const q=project(c.x,c.z);const p=trackAt(q.s,clamp(q.lateral,-5,5));c.x=p.x;c.z=p.z;c.heading=p.heading;c.speed=3;c.blocked=0;c.recoveries++;c.lastS=q.s;c.hit=.4;this.events.push({type:'recovery',car:c.id,time:this.time});}
 impact(c,type){if(c.hit<.1){c.collisions++;this.collisionCounts[type]++;}c.hit=.32;}
 step(dt,input={}){
  if(this.paused||this.phase==='results')return;dt=Math.min(dt,.025);
  if(this.phase==='countdown'){this.countdown-=dt;if(this.countdown<=0){this.phase='racing';this.countdown=0;}return;}
  this.time+=dt;
  for(const c of this.cars){c.hit=Math.max(0,c.hit-dt);const controls=c.id===0&&c.finishTime===null?input:this.ai(c,dt);let throttle=controls.throttle||0,brake=controls.brake||0;
   if(throttle)c.speed+=c.spec.accel*throttle*dt;
   if(brake){if(c.speed>1)c.speed=Math.max(0,c.speed-c.spec.brake*brake*dt);else if(c.id===0)c.speed=Math.max(-8,c.speed-c.spec.accel*.5*brake*dt);}
   const drag=.38+Math.abs(c.speed)*.016;c.speed-=Math.sign(c.speed)*Math.min(Math.abs(c.speed),drag*dt);c.speed=clamp(c.speed,-8,c.spec.max);
   c.steer+=((controls.steer||0)-c.steer)*Math.min(1,dt*7);
   const yaw=c.spec.grip*clamp(Math.abs(c.speed)/10,0,1)/(1+Math.abs(c.speed)*.017);
   c.heading+=c.steer*yaw*dt*Math.sign(c.speed);c.x+=Math.cos(c.heading)*c.speed*dt;c.z+=Math.sin(c.heading)*c.speed*dt;
  }
  // Multiple position passes resolve simultaneous impacts without letting cars tunnel through walls.
  for(let pass=0;pass<2;pass++){
   for(const c of this.cars){let q=project(c.x,c.z);const limit=HALF_WIDTH-1.45;if(Math.abs(q.lateral)>limit){const side=Math.sign(q.lateral),p=trackAt(q.s,side*limit);c.x=p.x;c.z=p.z;if(pass===0){c.speed*=.65;c.heading+=angleDelta(q.heading,c.heading)*.22;this.impact(c,'barrier');}}
    for(const o of OBSTACLES){const dx=c.x-o.x,dz=c.z-o.z,d=Math.hypot(dx,dz),r=1.45+o.r;if(d<r){const nx=d>.001?dx/d:1,nz=d>.001?dz/d:0;c.x=o.x+nx*r;c.z=o.z+nz*r;if(pass===0){c.speed*=-.18;this.impact(c,'obstacle');}}}
   }
   for(let i=0;i<this.cars.length;i++)for(let j=i+1;j<this.cars.length;j++){const a=this.cars[i],b=this.cars[j],dx=b.x-a.x,dz=b.z-a.z,d=Math.hypot(dx,dz),r=3.15;if(d<r){const nx=d>.001?dx/d:1,nz=d>.001?dz/d:0,depth=(r-d)/2+.002;a.x-=nx*depth;a.z-=nz*depth;b.x+=nx*depth;b.z+=nz*depth;if(pass===0){const va=a.speed*Math.cos(a.heading)*nx+a.speed*Math.sin(a.heading)*nz;const vb=b.speed*Math.cos(b.heading)*nx+b.speed*Math.sin(b.heading)*nz;if(va>vb){const impulse=(va-vb)*.65;a.speed-=impulse*(Math.cos(a.heading)*nx+Math.sin(a.heading)*nz);b.speed+=impulse*(Math.cos(b.heading)*nx+Math.sin(b.heading)*nz);}this.impact(a,'vehicle');this.impact(b,'vehicle');}}}
  }
  for(const c of this.cars){const q=project(c.x,c.z);if(c.finishTime===null){this.checkpoint(c,c.lastS,q.s);const previous=(c.nextCheckpoint-1)*LENGTH/CHECKPOINTS;const fromStart=((q.s-this.startS)%LENGTH+LENGTH)%LENGTH;const within=clamp(fromStart-previous,0,LENGTH/CHECKPOINTS);c.progress=c.lap*LENGTH+previous+within;}c.lastS=q.s;}
  if(this.player.finishTime!==null){this.phase='finishing';if(this.cars.every(c=>c.finishTime!==null))this.phase='results';}
 }
 snapshot(){return {phase:this.phase,paused:this.paused,time:this.time,countdown:this.countdown,selected:this.selected,collisions:{...this.collisionCounts},standings:this.ranking().map(c=>c.id),cars:this.cars.map(c=>({id:c.id,name:c.name,car:c.spec.id,x:c.x,z:c.z,speed:c.speed,heading:c.heading,completedLaps:c.lap,nextCheckpoint:c.nextCheckpoint,passedCheckpoints:c.passed,lapTimes:[...c.lapTimes],finishTime:c.finishTime,recoveries:c.recoveries,collisions:c.collisions,progress:c.progress}))};}
}
