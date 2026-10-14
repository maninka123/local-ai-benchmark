import * as THREE from 'three';

export class Car {
  constructor({color=0xff0000, maxSpeed=10, acceleration=5, braking=8, handling=0.05}){
    this.maxSpeed = maxSpeed;
    this.acceleration = acceleration;
    this.braking = braking;
    this.handling = handling;
    this.velocity = new THREE.Vector3();
    this.direction = new THREE.Vector3(0,0,1);
    const geometry = new THREE.BoxGeometry(2,1,4);
    const material = new THREE.MeshStandardMaterial({color});
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.castShadow=true;
    this.mesh.receiveShadow=true;
  }
  applyControls(accel,brake,steer,delta){
    // acceleration
    if(accel>0){
      const speed=this.velocity.length();
      const target=this.maxSpeed;
      const diff=target-speed;
      const accelStep=this.acceleration*delta;
      const add=Math.min(diff,accelStep);
      this.velocity.add(this.direction.clone().multiplyScalar(add));
    }
    // braking
    if(brake>0){
      const speed=this.velocity.length();
      const decel=this.braking*delta;
      const newSpeed=Math.max(0,speed-decel);
      this.velocity.setLength(newSpeed);
    }
    // steering
    if(steer!==0){
      const turnRate=this.handling*delta*steer;
      const quat=new THREE.Quaternion();
      quat.setFromAxisAngle(new THREE.Vector3(0,1,0),turnRate);
      this.direction.applyQuaternion(quat).normalize();
      this.mesh.rotation.y+=turnRate;
    }
    // friction
    const friction=2;
    const speed=this.velocity.length();
    if(speed>0){
      const f=friction*delta;
      if(f>speed) this.velocity.set(0,0,0);
      else this.velocity.multiplyScalar(1-f/speed);
    }
    // update position
    this.mesh.position.addScaledVector(this.velocity, delta);
  }
}
