import * as THREE from 'three';

export class Track {
  constructor() {
    this.trackRadius = 100;
    this.numSegments = 12;
    this.trackWidth = 10;
    this.trackHeight = 0.5;
    this.trackSegments = [];
    this.checkpoints = [];
    this.startFinishLine = null;
    this.setupTrack();
  }

  setupTrack() {
    // Create track segments
    for (let i = 0; i < this.numSegments; i++) {
      const angle = (i / this.numSegments) * 2 * Math.PI;
      const x = Math.cos(angle) * this.trackRadius;
      const z = Math.sin(angle) * this.trackRadius;
      const segment = new THREE.Mesh(
        new THREE.CylinderGeometry(0.5, 0.5, this.trackWidth, 8),
        new THREE.MeshStandardMaterial({ color: 0x000000 })
      );
      segment.position.set(x, 0, z);
      segment.rotation.x = Math.PI / 2;
      this.trackSegments.push(segment);
    }
    
    // Create checkpoints
    for (let i = 0; i < this.numSegments; i++) {
      const angle = (i / this.numSegments) * 2 * Math.PI;
      const x = Math.cos(angle) * this.trackRadius;
      const z = Math.sin(angle) * this.trackRadius;
      const checkpoint = new THREE.Mesh(
        new THREE.CylinderGeometry(0.2, 0.2, 0.5, 8),
        new THREE.MeshStandardMaterial({ color: 0xff0000 })
      );
      checkpoint.position.set(x, 0, z);
      checkpoint.rotation.x = Math.PI / 2;
      this.checkpoints.push(checkpoint);
    }
    
    // Create start/finish line
    this.startFinishLine = new THREE.Mesh(
      new THREE.BoxGeometry(2, 0.5, 0.5),
      new THREE.MeshStandardMaterial({ color: 0xffffff })
    );
    this.startFinishLine.position.set(0, 0, 0);
    this.startFinishLine.rotation.x = Math.PI / 2;
  }

  getTrackSegments() {
    return this.trackSegments;
  }

  getCheckpoints() {
    return this.checkpoints;
  }

  getStartFinishLine() {
    return this.startFinishLine;
  }

  getTrackRadius() {
    return this.trackRadius;
  }

  getNumSegments() {
    return this.numSegments;
  }

  getTrackWidth() {
    return this.trackWidth;
  }

  getTrackHeight() {
    return this.trackHeight;
  }
}