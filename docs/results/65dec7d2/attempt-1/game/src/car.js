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
  update(dt){
    // simple physics: apply velocity to position
    this.mesh.position.addScaledVector(this.velocity, dt);
    // apply friction
    const friction = 2;
    const speed = this.velocity.length();
    if(speed>0){
      const f = friction*dt;
      if(f>speed) this.velocity.set(0,0,0);
      else this.velocity.multiplyScalar(1-f/speed);
    }
  }
}
