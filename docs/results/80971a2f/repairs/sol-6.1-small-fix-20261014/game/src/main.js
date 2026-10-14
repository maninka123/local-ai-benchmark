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
const clock = new THREE.Clock();
function animate() {
  const dt = Math.min(clock.getDelta(), 0.05);
  requestAnimationFrame(animate);
  // Update controls
  if (keys['ArrowUp'] || keys['KeyW']) {
    carSpeed += acceleration * dt * 60 * (carSpeed < maxSpeed ? 1 : 0);
  }
  if (keys['ArrowDown'] || keys['KeyS']) {
    carSpeed -= acceleration * dt * 60 * (carSpeed > 0 ? 1 : 0);
    if (carSpeed < 0) carSpeed = 0;
  }
  // Steering
  if (keys['ArrowLeft'] || keys['KeyA']) {
    carDirection += maxTurnRate * dt * (carSpeed > 0 ? 1 : 0);
  }
  if (keys['ArrowRight'] || keys['KeyD']) {
    carDirection -= maxTurnRate * dt * (carSpeed > 0 ? 1 : 0);
  }

  // Apply movement
  car.rotation.y = carDirection;
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(car.quaternion);
  car.position.addScaledVector(forward, carSpeed * dt * 60);

  // Simple ground friction
  carSpeed *= Math.pow(1 - friction, dt * 60);

  // Update camera to chase car
  const offset = new THREE.Vector3(0, 5, 10);
  offset.applyQuaternion(car.quaternion);
  camera.position.copy(car.position).add(offset);
  camera.lookAt(car.position);

  // Chase camera is controlled above; OrbitControls would override its orientation.
  renderer.render(scene, camera);
}
animate();
