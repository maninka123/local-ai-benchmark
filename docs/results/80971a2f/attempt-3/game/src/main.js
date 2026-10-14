// Infrastructure only. Implement the game here.

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Create scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);

// Camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 5, 15);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Light
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(5, 10, 7);
scene.add(light);
scene.add(new THREE.AmbientLight(0x404040));

// Car (simple box)
const carGeometry = new THREE.BoxGeometry(2, 1, 4);
const carMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000 });
const car = new THREE.Mesh(carGeometry, carMaterial);
car.position.set(0, 0.5, 0);
scene.add(car);

// Player state
let keys = {};
let carSpeed = 0;
let carDirection = 0; // radians
const maxSpeed = 5;
const acceleration = 0.2;
const friction = 0.05;
const maxTurnRate = Math.PI / 180 * 30; // 30 deg per second

// Handle keys
window.addEventListener('keydown', (e) => {
  keys[e.code] = true;
});
window.addEventListener('keyup', (e) => {
  keys[e.code] = false;
});

// Game loop
function animate() {
  requestAnimationFrame(animate);
  // Update controls
  if (keys['ArrowUp'] || keys['w']) {
    carSpeed += acceleration * (carSpeed < maxSpeed ? 1 : 0);
  }
  if (keys['ArrowDown'] || keys['s']) {
    carSpeed -= acceleration * (carSpeed > 0 ? 1 : 0);
    if (carSpeed < 0) carSpeed = 0;
  }
  // Steering
  if (keys['ArrowLeft'] || keys['a']) {
    carDirection -= maxTurnRate * (carSpeed > 0 ? 1 : 0);
  }
  if (keys['ArrowRight'] || keys['d']) {
    carDirection += maxTurnRate * (carSpeed > 0 ? 1 : 0);
  }

  // Apply movement
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(car.quaternion);
  car.position.addScaledVector(forward, carSpeed);

  // Simple ground friction
  carSpeed *= 1 - friction;

  // Update camera to chase car
  const offset = new THREE.Vector3(0, 5, 10);
  offset.applyQuaternion(car.quaternion);
  camera.position.copy(car.position).add(offset);
  camera.lookAt(car.position);

  controls.update();
  renderer.render(scene, camera);
}
animate();
