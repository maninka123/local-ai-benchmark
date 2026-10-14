import * as THREE from 'three';
import { createTrack, waypoints } from './track.js';
import { Car } from './car.js';
import { NPC } from './npc.js';
import { CameraManager } from './camera.js';
import { UI } from './ui.js';
import { Race } from './race.js';
import { Controls } from './controls.js';

const scene = new THREE.Scene();
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lights are added in createTrack
createTrack(scene);

// Player car selection
const carSelection = new UI.CarSelection();
carSelection.onSelect = (carDef) => {
  if (playerCar) scene.remove(playerCar.mesh);
  playerCar = new Car(carDef);
  playerCar.mesh.position.set(0, 0.5, 0);
  scene.add(playerCar.mesh);
  race.setPlayerCar(playerCar);
};
carSelection.show();

let playerCar = null;
const npcCars = [];
for (let i = 0; i < 4; i++) {
  const npc = new NPC({ waypoints, speed: 8 + i });
  npc.mesh.position.set(0, 0.5, 0);
  scene.add(npc.mesh);
  npcCars.push(npc);
}

const cameraManager = new CameraManager(renderer.domElement, playerCar);
const ui = new UI.HUD();
const race = new Race({ waypoints, laps: 3, playerCar, npcCars, ui });
const controls = new Controls(playerCar, cameraManager, race);

window.addEventListener('resize', () => {
  cameraManager.onResize(window.innerWidth, window.innerHeight);
});

function animate(time) {
  const delta = time * 0.001;
  if (playerCar) playerCar.update(delta);
  npcCars.forEach(npc => npc.update(delta));
  race.update(delta);
  cameraManager.update(delta);
  ui.update();
  renderer.render(scene, cameraManager.camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
