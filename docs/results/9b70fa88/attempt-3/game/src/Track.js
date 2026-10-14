import * as THREE from 'three';

class Track {
  constructor() {
    this.scene = new THREE.Scene();
    this.createTrack();
  }

  createTrack() {
    const trackGeometry = new THREE.CylinderGeometry(10, 10, 0.1, 64);
    const trackMaterial = new THREE.MeshStandardMaterial({ color: 0x808080 });
    const track = new THREE.Mesh(trackGeometry, trackMaterial);
    track.rotation.x = Math.PI / 2;
    this.scene.add(track);
  }
}

export default Track;