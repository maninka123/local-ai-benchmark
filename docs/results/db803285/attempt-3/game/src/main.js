import * as THREE from 'three';
import { config, carSpecs, trackPoints } from './config.js';
import { createTrack } from './track.js';
import { createCar } from './car.js';
import { checkCollisions } from './collision.js';

// Game state
let gameState = {
  screen: 'menu',
  selectedCarIndex: 0,
  playerCar: null,
  npcCars: [],
  checkpoints: [],
  cameraMode: 0,
  paused: false,
  time: 0,
  raceStarted: false,
  lastCheckpointIndex: -1
};

// Three.js scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 200, 500);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
sunLight.position.set(100, 200, 50);
sunLight.castShadow = true;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 500;
sunLight.shadow.camera.left = -200;
sunLight.shadow.camera.right = 200;
sunLight.shadow.camera.top = 200;
sunLight.shadow.camera.bottom = -200;
scene.add(sunLight);

// Create track
const trackCurve = createTrack(scene);

// Car class
function createCarObject(spec) {
  const carGroup = new THREE.Group();
  
  let bodyGeometry;
  if (spec.name === 'Speedster') {
    bodyGeometry = new THREE.BoxGeometry(2.2, 0.8, 4.5);
  } else if (spec.name === 'Steady') {
    bodyGeometry = new THREE.BoxGeometry(2.0, 1.0, 4.0);
  } else {
    bodyGeometry = new THREE.BoxGeometry(2.4, 0.9, 4.2);
  }
  
  const bodyMaterial = new THREE.MeshStandardMaterial({ color: spec.color });
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
  body.position.y = 0.5;
  body.castShadow = true;
  carGroup.add(body);
  
  const cabinGeometry = new THREE.BoxGeometry(
    spec.name === 'Drifter' ? 1.6 : 1.8,
    0.6,
    2
  );
  const cabinMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
  const cabin = new THREE.Mesh(cabinGeometry, cabinMaterial);
  cabin.position.set(0, 1.2, -0.5);
  carGroup.add(cabin);
  
  const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
  const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x111111 });
  
  const positions = [
    { x: -1, z: 1.2 },
    { x: 1, z: 1.2 },
    { x: -1, z: -1.2 },
    { x: 1, z: -1.2 }
  ];
  
  positions.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(pos.x, 0.4, pos.z);
    carGroup.add(wheel);
  });
  
  const lightGeometry = new THREE.BoxGeometry(0.3, 0.2, 0.1);
  const lightMaterial = new THREE.MeshBasicMaterial({ color: 0xffffaa });
  const leftLight = new THREE.Mesh(lightGeometry, lightMaterial);
  leftLight.position.set(-0.6, 0.5, 2.01);
  carGroup.add(leftLight);
  
  const rightLight = new THREE.Mesh(lightGeometry, lightMaterial);
  rightLight.position.set(0.6, 0.5, 2.01);
  carGroup.add(rightLight);
  
  const tailLightMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
  const leftTail = new THREE.Mesh(lightGeometry, tailLightMaterial);
  leftTail.position.set(-0.6, 0.5, -2.01);
  carGroup.add(leftTail);
  
  const rightTail = new THREE.Mesh(lightGeometry, tailLightMaterial);
  rightTail.position.set(0.6, 0.5, -2.01);
  carGroup.add(rightTail);
  
  return {
    mesh: carGroup,
    spec: spec,
    position: new THREE.Vector3(),
    velocity: new THREE.Vector3(),
    acceleration: spec.acceleration,
    maxSpeed: spec.maxSpeed,
    braking: spec.braking,
    handling: spec.handling,
    checkpointIndex: -1
  };
}

// Initialize game
function initGame() {
  gameState.playerCar = createCarObject(carSpecs[gameState.selectedCarIndex]);
  
  for (let i = 0; i < config.npcCount; i++) {
    const specIndex = (i + 1) % carSpecs.length;
    const npcCar = createCarObject(carSpecs[specIndex]);
    const angle = (i / config.npcCount) * Math.PI * 2 + 0.5;
    npcCar.position.set(
      config.trackRadius + 150 * Math.cos(angle),
      0,
      config.trackRadius + 150 * Math.sin(angle)
    );
    npcCar.velocity.set(0, 0, 15);
    gameState.npcCars.push(npcCar);
  }
  
  for (let i = 0; i < config.checkpointInterval; i++) {
    const angle = (i / config.checkpointInterval) * Math.PI * 2;
    const checkpoint = {
      position: new THREE.Vector3(
        config.trackRadius + 150 * Math.cos(angle),
        0,
        config.trackRadius + 150 * Math.sin(angle)
      ),
      passed: false
    };
    gameState.checkpoints.push(checkpoint);
  }
  
  updateCamera();
}

function updateCamera() {
  const player = gameState.playerCar.mesh;
  
  switch(gameState.cameraMode) {
    case 0:
      camera.position.set(
        player.position.x + Math.sin(player.rotation.y) * 15,
        player.position.y + 3,
        player.position.z + Math.cos(player.rotation.y) * 15
      );
      camera.lookAt(player.position);
      break;
    case 1:
      camera.position.set(
        player.position.x + Math.sin(player.rotation.y) * 2,
        player.position.y + 0.8,
        player.position.z + Math.cos(player.rotation.y) * 2
      );
      camera.lookAt(
        player.position.x + Math.sin(player.rotation.y + 0.1) * 5,
        player.position.y + 2,
        player.position.z + Math.cos(player.rotation.y + 0.1) * 5
      );
      break;
    case 2:
      camera.position.set(
        player.position.x + Math.sin(player.rotation.y) * 40,
        player.position.y + 30,
        player.position.z + Math.cos(player.rotation.y) * 40
      );
      camera.lookAt(player.position);
      break;
  }
}

function togglePause() {
  gameState.paused = !gameState.paused;
  if (!gameState.paused) {
    gameState.screen = 'race';
  }
}

function updatePlayerCar(dt) {
  const player = gameState.playerCar;
  
  player.position.add(player.velocity.clone().multiplyScalar(dt));
  player.velocity.multiplyScalar(0.98);
  
  const speed = player.velocity.length();
  if (speed > player.maxSpeed) {
    player.velocity.normalize().multiplyScalar(player.maxSpeed);
  }
  
  const closestPoint = trackCurve.getClosestPointTo(new THREE.Vector3(
    player.position.x, 0, player.position.z
  ));
  
  const tangent = trackCurve.getTangentAt(closestPoint);
  
  const projectedVelocity = new THREE.Vector3()
    .copy(player.velocity)
    .projectOnto(tangent);
  
  player.velocity.copy(projectedVelocity);
}

function updateNPCCars(dt) {
  gameState.npcCars.forEach(npc => {
    const closestPoint = trackCurve.getClosestPointTo(new THREE.Vector3(
      npc.position.x, 0, npc.position.z
    ));
    
    const tangent = trackCurve.getTangentAt(closestPoint);
    
    const projectedVelocity = new THREE.Vector3()
      .copy(npc.velocity)
      .projectOnto(tangent);
    
    npc.velocity.copy(projectedVelocity);
    
    npc.position.add(npc.velocity.clone().multiplyScalar(dt));
  });
}

function checkCheckpoints() {
  const player = gameState.playerCar;
  let checkpointIndex = -1;
  
  for (let i = 0; i < gameState.checkpoints.length; i++) {
    const cp = gameState.checkpoints[i];
    if (player.position.distanceTo(cp.position) < 30) {
      checkpointIndex = i;
      break;
    }
  }
  
  if (checkpointIndex !== -1 && checkpointIndex > gameState.lastCheckpointIndex) {
    gameState.lastCheckpointIndex = checkpointIndex;
  }
}

function setupControls() {
  document.addEventListener('keydown', (e) => {
    if (gameState.screen !== 'race') return;
    
    switch(e.key.toLowerCase()) {
      case 'w':
      case 'arrowup':
        gameState.playerCar.velocity.y += gameState.playerCar.acceleration;
        break;
      case 's':
      case 'arrowdown':
        gameState.playerCar.velocity.y -= gameState.playerCar.braking;
        break;
      case 'a':
      case 'arrowleft':
        gameState.playerCar.mesh.rotation.y += 0.05 / gameState.playerCar.handling;
        break;
      case 'd':
      case 'arrowright':
        gameState.playerCar.mesh.rotation.y -= 0.05 / gameState.playerCar.handling;
        break;
      case 'c':
        gameState.cameraMode = (gameState.cameraMode + 1) % 3;
        updateCamera();
        break;
      case 'p':
      case 'escape':
        togglePause();
        break;
      case 'r':
        location.reload();
        break;
    }
  });
}

function createHUD() {
  const hud = document.createElement('div');
  hud.style.cssText = 'position:absolute;top:10px;left:10px;color:white;font-family:sans-serif;font-size:14px;pointer-events:none;';
  
  hud.innerHTML = `
    <div>Speed: <span id="speed">0</span> km/h</div>
    <div>Lap: <span id="lap">0</span>/3</div>
    <div>Position: <span id="position">1</span></div>
    <div>Time: <span id="time">0.000</span>s</div>
    <div>Camera: <span id="camera">Chase</span></div>
  `;
  
  document.body.appendChild(hud);
  return {
    speed: document.getElementById('speed'),
    lap: document.getElementById('lap'),
    position: document.getElementById('position'),
    time: document.getElementById('time'),
    camera: document.getElementById('camera')
  };
}

function updateHUD() {
  const speed = Math.round(gameState.playerCar.velocity.length() * 3.6);
  hud.speed.textContent = speed;
  hud.time.textContent = (gameState.time / 1000).toFixed(3);
  
  if (gameState.lastCheckpointIndex >= config.checkpointInterval - 1) {
    gameState.lap++;
    gameState.lastCheckpointIndex = -1;
  }
  
  hud.lap.textContent = gameState.lap;
}

function updatePositions() {
  const allCars = [gameState.playerCar, ...gameState.npcCars];
  allCars.sort((a, b) => {
    const aAngle = Math.atan2(a.position.z, a.position.x);
    const bAngle = Math.atan2(b.position.z, b.position.x);
    return aAngle - bAngle;
  });
  
  hud.position.textContent = allCars.indexOf(gameState.playerCar) + 1;
}

let hud;
let lastTime = performance.now();

function animate() {
  requestAnimationFrame(animate);
  
  if (!gameState.paused && gameState.screen === 'race') {
    const now = performance.now();
    const dt = (now - lastTime) / 1000;
    lastTime = now;
    
    gameState.time += dt * 1000;
    
    updatePlayerCar(dt);
    updateNPCCars(dt);
    checkCollisions(gameState.playerCar, gameState.npcCars, []);
    checkCheckpoints();
    updateCamera();
    updateHUD();
    updatePositions();
    
    renderer.render(scene, camera);
  }
}

// Initialize
initGame();
hud = createHUD();
setupControls();
animate();
