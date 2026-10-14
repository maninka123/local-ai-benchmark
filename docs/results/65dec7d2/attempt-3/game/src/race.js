import * as THREE from 'three';

export class Race {
  constructor({waypoints,laps=3,playerCar,npcCars,ui}){
    this.waypoints=waypoints;
    this.laps=laps;
    this.playerCar=playerCar;
    this.npcCars=npcCars;
    this.ui=ui;
    this.paused=false;
    this.startTime=performance.now();
    this.lapTimes=[];
    this.currentLap=1;
    this.checkpointIndex=0;
    this.finished=false;
  }
  update(delta){
    if(this.paused||this.finished) return;
    // simple checkpoint logic: when player passes waypoint index
    const pos=this.playerCar.mesh.position;
    const target=this.waypoints[this.checkpointIndex];
    if(pos.distanceTo(target)<2){
      this.checkpointIndex=(this.checkpointIndex+1)%this.waypoints.length;
      if(this.checkpointIndex===0){
        this.currentLap++;
        this.lapTimes.push(performance.now()-this.startTime);
        this.startTime=performance.now();
        if(this.currentLap>this.laps){
          this.finished=true;
        }
      }
    }
    // update HUD
    this.ui.speed=this.playerCar.velocity.length();
    this.ui.lap=this.currentLap;
    this.ui.position=1; // placeholder
    this.ui.time=(performance.now()-this.startTime)/1000;
    this.ui.camera=this.playerCar.cameraView||'Chase';
  }
  togglePause(){this.paused=!this.paused;}
  restart(){
    this.paused=false;
    this.finished=false;
    this.currentLap=1;
    this.checkpointIndex=0;
    this.startTime=performance.now();
    this.lapTimes=[];
    this.playerCar.mesh.position.set(0,0.5,0);
    this.playerCar.velocity.set(0,0,0);
  }
}
