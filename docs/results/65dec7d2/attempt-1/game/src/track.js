import * as THREE from 'three';

export const waypoints = [];
const radius = 20;
const segments = 36;
for (let i = 0; i < segments; i++) {
  const angle = (i / segments) * Math.PI * 2;
  const x = Math.cos(angle) * radius;
  const z = Math.sin(angle) * radius;
  waypoints.push(new THREE.Vector3(x, 0, z));
}

export function createTrack(scene) {
  const innerRadius = 18;
  const outerRadius = 22;
  const geometry = new THREE.RingGeometry(innerRadius, outerRadius, 64, 1, 0, Math.PI * 2);
  const material = new THREE.MeshStandardMaterial({ color: 0x555555 });
  const track = new THREE.Mesh(geometry, material);
  track.rotation.x = -Math.PI / 2;
  scene.add(track);

  const lineGeom = new THREE.PlaneGeometry(2, 10);
  const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
  const line = new THREE.Mesh(lineGeom, lineMat);
  line.rotation.x = -Math.PI / 2;
  line.position.set(0, 0.01, -innerRadius - 0.5);
  scene.add(line);

  const boundaryGeom = new THREE.BoxGeometry(1, 2, outerRadius * 2);
  const boundaryMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
  const leftBoundary = new THREE.Mesh(boundaryGeom, boundaryMat);
  leftBoundary.position.set(-innerRadius - 0.5, 0.5, 0);
  leftBoundary.rotation.y = Math.PI / 2;
  scene.add(leftBoundary);

  const rightBoundary = leftBoundary.clone();
  rightBoundary.position.set(innerRadius + 0.5, 0.5, 0);
  scene.add(rightBoundary);

  const ambient = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambient);
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(5, 10, 5);
  scene.add(dirLight);
}
