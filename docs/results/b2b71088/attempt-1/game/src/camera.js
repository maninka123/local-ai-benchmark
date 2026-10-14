export default class CameraController {
  constructor(player, camera) {
    this.player = player;
    this.camera = camera;
    this.views = { chase: 'chase', hood: 'hood', overhead: 'overhead' };
    this.current = 'chase';
    this offsets = {
      chase: { x: 0, y: 2, z: -10 },
      hood: { x: 0, y: 1.5, z: -2 },
      overhead: { x: 0, y: 30, z: 0 }
    };
  }
  update() {
    const view = this.offsets[this.current];
    const playerPos = this.player.position;
    const forward = new THREE.Vector3();
    this.player.getWorldDirection(forward);
    const height = view.y + Math.sin(Date.now() * 0.001) * 0.1;
    const newPos = playerPos.clone();
    newPos.x += forward.x * -view.z;
    newPos.y += height;
    newPos.z += forward.z * -view.z;
    this.camera.position.lerp(newPos, 0.1);
    this.camera.lookAt(playerPos);
  }
  setView(v) { if (this.views[v]) this.current = v; }
}
