export default class Car {
  constructor(scene, position, color = 0xff0000) {
    this.scene = scene;
    this.mesh = new THREE.Mesh(
      new THREE.BoxGeometry(2, 1, 4),
      new THREE.MeshStandardMaterial({ color })
    );
    this.mesh.position.copy(position);
    scene.add(this.mesh);
  }

  update() {
    // Basic movement logic will be added later
  }
}