import * as THREE from 'three';

export class NPC {
  constructor({waypoints, speed=8}){
    this.waypoints = waypoints;
    this.speed = speed;
    this.currentIndex = 0;
    const geometry = new THREE.BoxGeometry(2,1,4);
    const material = new THREE.MeshStandardMaterial({color:0x00ff00});
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.castShadow=true;
    this.mesh.receiveShadow=true;
    this.velocity = new THREE.Vector3();
  }
  update(dt){
    const target = this.waypoints[this.currentIndex];
    const dir = new THREE.Vector3().subVectors(target, this.mesh.position).normalize();
    const distance = this.mesh.position.distanceTo(target);
    if(distance<1){
      this.currentIndex = (this.currentIndex+1)%this.waypoints.length;
    }
    this.velocity.copy(dir).multiplyScalar(this.speed);
    this.mesh.position.addScaledVector(this.velocity, dt);
    this.mesh.lookAt(target);
  }
}
