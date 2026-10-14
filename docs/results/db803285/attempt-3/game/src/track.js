import * as THREE from 'three';

export function createTrack(scene) {
  const trackCurve = new THREE.CatmullRomCurve3(
    [
      { x: 0, y: 0, z: -200 },
      { x: 200, y: 0, z: -100 },
      { x: 200, y: 0, z: 100 },
      { x: 0, y: 0, z: 200 },
      { x: -200, y: 0, z: 100 },
      { x: -200, y: 0, z: -100 }
    ],
    {
      closed: true,
      closedLoopPoints: 64
    }
  );
  
  const trackWidth = 30;
  const roadMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
  const grassMaterial = new THREE.MeshStandardMaterial({ color: 0x2d5a27 });
  
  // Create road
  const roadGeometry = new THREE.TubeGeometry(trackCurve, 64, trackWidth / 2, 16, false);
  const road = new THREE.Mesh(roadGeometry, roadMaterial);
  road.position.y = -0.5;
  scene.add(road);
  
  // Create grass
  const groundGeometry = new THREE.PlaneGeometry(800, 800);
  const ground = new THREE.Mesh(groundGeometry, grassMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -1;
  scene.add(ground);
  
  // Add barriers
  const barrierGeometry = new THREE.BoxGeometry(4, 3, 0.5);
  const barrierMaterial = new THREE.MeshStandardMaterial({ color: 0xff6600 });
  
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2;
    const x = 250 * Math.cos(angle);
    const z = 250 * Math.sin(angle);
    const barrier = new THREE.Mesh(barrierGeometry, barrierMaterial);
    barrier.position.set(x, 1.5, z);
    scene.add(barrier);
  }
  
  // Add start/finish line
  const startLineGeometry = new THREE.PlaneGeometry(40, 2);
  const startLineMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const startLine = new THREE.Mesh(startLineGeometry, startLineMaterial);
  startLine.rotation.x = -Math.PI / 2;
  startLine.position.set(0, 0.01, -200);
  scene.add(startLine);
  
  // Add checkpoints
  const checkpointPositions = [];
  for (let i = 0; i < 8; i++) {
    const angle = (i / 8) * Math.PI * 2;
    const x = 200 * Math.cos(angle);
    const z = 200 * Math.sin(angle);
    checkpointPositions.push({ x, z });
  }
  
  return {
    curve: trackCurve,
    getClosestPointTo: (point) => {
      const closest = trackCurve.getClosestPoint(point);
      return closest;
    },
    getTangentAt: (point) => {
      const tangent = trackCurve.getTangent(point);
      return tangent;
    }
  };
}
