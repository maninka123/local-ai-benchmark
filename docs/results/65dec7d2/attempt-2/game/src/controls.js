import * as THREE from 'three';

export class Controls {
  constructor(playerCar, cameraManager, race){
    this.car=playerCar;
    this.cameraManager=cameraManager;
    this.race=race;
    this.keys={};
    window.addEventListener('keydown',e=>{this.keys[e.key.toLowerCase()]=true;});
    window.addEventListener('keyup',e=>{this.keys[e.key.toLowerCase()]=false;});
    window.addEventListener('keydown',e=>{if(e.key==='c')this.cameraManager.switchView();});
    window.addEventListener('keydown',e=>{if(e.key==='p'||e.key==='Escape')this.race.togglePause();});
    window.addEventListener('keydown',e=>{if(e.key==='r')this.race.restart();});
  }
  update(delta){
    if(!this.car) return;
    const accel=this.keys['w']||this.keys['arrowup']?1:0;
    const brake=this.keys['s']||this.keys['arrowdown']?1:0;
    const steer=this.keys['a']||this.keys['arrowleft']?-1:0;
    const steerRight=this.keys['d']||this.keys['arrowright']?1:0;
    const steerDir=steer+steerRight;
    this.car.applyControls(accel,brake,steerDir,delta);
  }
}
