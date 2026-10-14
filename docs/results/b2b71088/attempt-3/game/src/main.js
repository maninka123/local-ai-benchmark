import * as THREE from 'three';
import Car from './car.js';
import NPC from './npc.js';
import Input from './input.js';
import Camera from './camera.js';

// Basic scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 10);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Simple track geometry (plane)
const trackGeometry = new THREE.PlaneGeometry(200, 200);
const trackMaterial = new THREE.MeshStandardMaterial({ color: 0x228B22 });
const track = new THREE.Mesh(trackGeometry, trackMaterial);
track.rotation.x = -Math.PI / 2;
track.receiveShadow = true;
scene.add(track);

// Create player car and NPC cars
const playerCar = new Car('player');
playerCar.position.set(0, 1, 0);
scene.add(playerCar);

const npcCars = [new NPC('npc1'), new NPC('npc2'), new NPC('npc3'), new NPC('npc4')].map(n => {
  n.position.set(Math.random() * 80 - 40, 1, Math.random() * 80 - 40);
  scene.add(n);
  return n;
});

// Input and camera controllers
const input = new Input(playerCar);
const cameraCtrl = new Camera(playerCar, camera);

// Animation loop
function animate(time) {
  requestAnimationFrame(animate);
  const delta = time - (animate.lastTime || time);
  animate.lastTime = time;

  input.update();
  npcCars.forEach(n => n.update(delta));
  playerCar.update(input, delta);
  cameraCtrl.update();

  renderer.render(scene, camera);
}
animate();
