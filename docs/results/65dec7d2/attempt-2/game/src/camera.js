import * as THREE from 'three';

export class CameraManager {
  constructor(dom, playerCar){
    this.dom=dom;
    this.playerCar=playerCar;
    this.cameras={};
    this.current='chase';
    this.initCameras();
    this.onResize(window.innerWidth, window.innerHeight);
  }
  initCameras(){
    const fov=75; const aspect=window.innerWidth/window.innerHeight; const near=0.1; const far=2000;
    // chase
    const chase=new THREE.PerspectiveCamera(fov,aspect,near,far);
    chase.position.set(0,5,-10);
    chase.lookAt(0,0,0);
    this.cameras.chase=chase;
    // cockpit
    const cockpit=new THREE.PerspectiveCamera(fov,aspect,near,far);
    cockpit.position.set(0,1,0.5);
    cockpit.lookAt(0,0,5);
    this.cameras.cockpit=cockpit;
    // overhead
    const overhead=new THREE.PerspectiveCamera(fov,aspect,near,far);
    overhead.position.set(0,30,0);
    overhead.lookAt(0,0,0);
    this.cameras.overhead=overhead;
    this.camera=this.cameras[this.current];
  }
  switch(){
    this.current=this.current==='chase'?'cockpit':this.current==='cockpit'?'overhead':'chase';
    this.camera=this.cameras[this.current];
  }
  onResize(w,h){
    const aspect=w/h;
    Object.values(this.cameras).forEach(cam=>{cam.aspect=aspect;cam.updateProjectionMatrix();});
  }
  update(delta){
    if(!this.playerCar) return;
    const pos=this.playerCar.mesh.position;
    const dir=this.playerCar.direction;
    const chase=this.cameras.chase;
    chase.position.copy(pos).add(new THREE.Vector3(-dir.x*10,-5,-dir.z*10));
    chase.lookAt(pos);
    const cockpit=this.cameras.cockpit;
    cockpit.position.copy(pos).add(new THREE.Vector3(0,1,0.5));
    cockpit.lookAt(pos.clone().add(dir.clone().multiplyScalar(5)));
    const overhead=this.cameras.overhead;
    overhead.position.copy(pos).add(new THREE.Vector3(0,30,0));
    overhead.lookAt(pos);
  }
}
