import * as THREE from 'three';

export class Track {
  constructor(scene) {
    this.scene = scene;
    this.checkpoints = [];
    this.mesh = new THREE.Group();
    this.scene.add(this.mesh);
    this.buildTrack();
  }

  buildTrack() {
    // Define checkpoints (x, z)
    this.checkpoints = [
      { x: 0, z: 0 },
      { x: 50, z: 0 },
      { x: 80, z: 40 },
      { x: 60, z: 80 },
      { x: 0, z: 80 },
      { x: -40, z: 60 },
      { x: -40, z: 0 },
      { x: 0, z: 0 } // Back to start
    ];

    // Road Geometry
    const roadWidth = 12;
    const roadLength = 100;
    const roadGeo = new THREE.PlaneGeometry(roadLength, roadWidth);
    const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
    const road = new THREE.Mesh(roadGeo, roadMat);
    road.rotation.x = -Math.PI / 2;
    road.position.set(0, 0.01, 0);
    this.mesh.add(road);

    // Start/Finish line
    const startGeo = new THREE.PlaneGeometry(20, 5);
    const startMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const startLine = new THREE.Mesh(startGeo, startMat);
    startLine.rotation.x = -Math.PI / 2;
    startLine.position.set(-length/2, 0.02, 0);
    this.mesh.add(startLine);

    // Barriers (Visual only for now)
    const barrierGeo = new THREE.BoxGeometry(2, 1, 0.5);
    const barrierMat = new THREE.MeshStandardMaterial({ color: 0xff0000 });
    
    // Add barriers along the track
    const barrierPositions = [
      { x: 25, z: 0 }, { x: 65, z: 0 },
      { x: 80, z: 20 }, { x: 80, z: 60 },
      { x: 60, z: 80 }, { x: 20, z: 80 },
      { x: 0, z: 60 }, { x: 0, z: 20 },
      { x: -20, z: 0 }, { x: -20, z: 40 }
    ];

    barrierPositions.forEach(pos => {
      const barrier = new THREE.Mesh(barrierGeo, barrierMat);
      barrier.position.set(pos.x, 0.5, pos.z);
      this.mesh.add(barrier);
    });

    // Scenery (Trees)
    const treeGeo = new THREE.ConeGeometry(1, 4, 8);
    const treeMat = new THREE.MeshStandardMaterial({ color: 0x228b22 });
    const trunkGeo = new THREE.CylinderGeometry(0.3, 0.3, 1);
    const trunkMat = new THREE.MeshStandardMaterial({ color: 0x8b4513 });

    for (let i = 0; i < 20; i++) {
      const tree = new THREE.Group();
      const leaves = new THREE.Mesh(treeGeo, treeMat);
      leaves.position.y = 2;
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.y = 0.5;
      tree.add(leaves, trunk);
      
      // Random positions outside the road
      const angle = Math.random() * Math.PI * 2;
      const dist = 30 + Math.random() * 50;
      tree.position.set(Math.cos(angle) * dist, 0, Math.sin(angle) * dist);
      this.mesh.add(tree);
    }
  }

  getCheckpointPosition(index) {
    return this.checkpoints[index % this.checkpoints.length];
  }

  checkCollisions(player) {
    // Simple distance check against barriers
    // If player is too close to a barrier, push them back
    // This is a simplified arcade collision
  }
}
