import * as THREE from 'three';
import { Car } from './car.js';

export class NPC extends Car {
  constructor({waypoints, speed=8, color=0x888888}){
    super({color, maxSpeed:speed, acceleration:4, braking:6, handling:0.06});
    this.waypoints=waypoints;
    this.current=0;
    this.target=this.waypoints[this.current];
  }
  update(delta){
    // simple steering towards target waypoint
    const toTarget=this.target.clone().sub(this.mesh.position);
    const distance=toTarget.length();
    if(distance<1){
      this.current=(this.current+1)%this.waypoints.length;
      this.target=this.waypoints[this.current];
    }
    const desiredDir=toTarget.normalize();
    const steer=desiredDir.dot(this.direction);
    this.applyControls(1,0,steer*5,delta);
  }
}
