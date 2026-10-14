// ==================== ARCADE RACING GAME ====================
import * as THREE from 'three';

// ==================== CONSTANTS ====================
const TRACK_WIDTH = 14;
const TRACK_SMOOTH_COUNT = 800;
const CHECKPOINT_COUNT = 6;
const TOTAL_LAPS = 3;
const NUM_NPCS = 4;
const COUNTDOWN_TIME = 3;

// ==================== CAR DEFINITIONS ====================
const CAR_DEFS = [
  { name: "Thunder GT", color: 0xcc2222, accentColor: 0xff6644, maxSpeed: 95, acceleration: 42, braking: 38, handling: 3.2 },
  { name: "Storm Racer", color: 0x2244cc, accentColor: 0x4488ff, maxSpeed: 105, acceleration: 35, braking: 35, handling: 2.8 },
  { name: "Phantom X", color: 0x22aa44, accentColor: 0x66ff88, maxSpeed: 88, acceleration: 48, braking: 42, handling: 3.8 }
];

// ==================== GAME STATE ====================
let scene, camera, renderer;
let playerCar = null;
let npcCars = [];
let trackCurve, TRACK_SMOOTH, TRACK_NORMALS, TRACK_TANGENTS;
let gameState = "menu"; // menu, selection, countdown, racing, paused, results
let raceStarted = false;
let raceTimer = 0;
let countdownTimer = 0;
let selectedCarIndex = 0;
let cameraMode = 0;
let keys = {};
let clock;
let barriers = [];
let trees = [];
let checkpoints = [];
let raceFinished = false;
let finishPositions = [];
let playerLapProgress = 0;
let playerLastCheckpoint = -1;
let npcLapProgresses = [];
let npcLastCheckpoints = [];
let countdownPhase = "";
let lastFrameTime = 0;

// ==================== UI ELEMENTS ====================
let uiElements = {};

function createUI() {
  // Main menu
  const menuDiv = document.createElement('div');
  menuDiv.id = 'menu';
  menuDiv.style.cssText = `position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:100;font-family:'Segoe UI',Arial,sans-serif;`;
  menuDiv.innerHTML = `
    <h1 style="color:#fff;font-size:72px;margin-bottom:10px;text-shadow:0 0 30px rgba(255,100,0,0.8);letter-spacing:4px;">ARCADE RACING</h1>
    <p style="color:#aaa;font-size:18px;margin-bottom:40px;">Select your car and race against opponents!</p>
    <button id="startBtn" style="padding:15px 50px;font-size:24px;background:linear-gradient(45deg,#ff6b35,#f7c948);border:none;border-radius:8px;cursor:pointer;color:#fff;font-weight:bold;text-shadow:1px 1px 2px rgba(0,0,0,0.5);box-shadow:0 4px 15px rgba(255,107,53,0.4);transition:transform 0.2s;">START RACE</button>
    <button id="controlsBtn" style="padding:12px 40px;font-size:18px;background:rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.3);border-radius:8px;cursor:pointer;color:#fff;margin-top:20px;transition:background 0.2s;">CONTROLS</button>
    <div id="controlsInfo" style="display:none;margin-top:30px;padding:20px;background:rgba(0,0,0,0.5);border-radius:10px;color:#fff;font-size:16px;line-height:1.8;">
      <h3 style="color:#f7c948;">Controls</h3>
      <p>W / Up Arrow - Accelerate<br>S / Down Arrow - Brake/Reverse<br>A / Left Arrow - Steer Left<br>D / Right Arrow - Steer Right<br>C - Change Camera<br>P / Escape - Pause/Resume<br>R - Restart Race</p>
    </div>
  `;
  document.body.appendChild(menuDiv);

  // Car selection
  const selectDiv = document.createElement('div');
  selectDiv.id = 'carSelect';
  selectDiv.style.cssText = `position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);display:none;flex-direction:column;align-items:center;justify-content:center;z-index:100;font-family:'Segoe UI',Arial,sans-serif;`;
  selectDiv.innerHTML = `
    <h2 style="color:#fff;font-size:48px;margin-bottom:30px;">SELECT YOUR CAR</h2>
    <div id="carOptions" style="display:flex;gap:30px;margin-bottom:40px;"></div>
    <button id="raceBtn" style="padding:15px 50px;font-size:24px;background:linear-gradient(45deg,#ff6b35,#f7c948);border:none;border-radius:8px;cursor:pointer;color:#fff;font-weight:bold;display:none;">START RACE</button>
  `;
  document.body.appendChild(selectDiv);

  // HUD
  const hudDiv = document.createElement('div');
  hudDiv.id = 'hud';
  hudDiv.style.cssText = `position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;display:none;z-index:50;font-family:'Segoe UI',Arial,sans-serif;`;
  hudDiv.innerHTML = `
    <div id="hudTop" style="position:absolute;top:20px;left:20px;color:#fff;background:rgba(0,0,0,0.6);padding:15px;border-radius:8px;font-size:18px;line-height:1.8;">
      <div>Speed: <span id="speedDisplay">0</span> km/h</div>
      <div>Lap: <span id="lapDisplay">0</span> / ${TOTAL_LAPS}</div>
      <div>Position: <span id="posDisplay">1st</span></div>
      <div>Time: <span id="timeDisplay">0:00.00</span></div>
    </div>
    <div id="hudBottom" style="position:absolute;bottom:20px;left:50%;transform:translateX(-50%);color:#fff;background:rgba(0,0,0,0.6);padding:10px 30px;border-radius:8px;font-size:24px;text-align:center;">
      Camera: <span id="camDisplay">Chase</span>
    </div>
    <div id="countdownDisplay" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#fff;font-size:120px;font-weight:bold;display:none;text-shadow:0 0 40px rgba(255,100,0,0.8);"></div>
    <div id="pauseOverlay" style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:none;flex-direction:column;align-items:center;justify-content:center;z-index:60;">
      <h2 style="color:#fff;font-size:64px;margin-bottom:30px;">PAUSED</h2>
      <p style="color:#aaa;font-size:20px;">Press P or Escape to resume</p>
    </div>
  `;
  document.body.appendChild(hudDiv);

  // Results screen
  const resultsDiv = document.createElement('div');
  resultsDiv.id = 'results';
  resultsDiv.style.cssText = `position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);display:none;flex-direction:column;align-items:center;justify-content:center;z-index:100;font-family:'Segoe UI',Arial,sans-serif;`;
  resultsDiv.innerHTML = `
    <h2 style="color:#fff;font-size:56px;margin-bottom:30px;">RACE RESULTS</h2>
    <div id="resultsList" style="background:rgba(0,0,0,0.5);padding:30px;border-radius:10px;color:#fff;font-size:24px;line-height:2;min-width:400px;"></div>
    <button id="restartBtn" style="padding:15px 50px;font-size:24px;background:linear-gradient(45deg,#ff6b35,#f7c948);border:none;border-radius:8px;cursor:pointer;color:#fff;font-weight:bold;margin-top:30px;">RACE AGAIN</button>
    <button id="menuBtn" style="padding:12px 40px;font-size:18px;background:rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.3);border-radius:8px;cursor:pointer;color:#fff;margin-top:15px;">MAIN MENU</button>
  `;
  document.body.appendChild(resultsDiv);

  uiElements = { menu: menuDiv, select: selectDiv, hud: hudDiv, results: resultsDiv };
}

// ==================== TRACK GENERATION ====================
function generateTrack() {
  const points = [
    new THREE.Vector3(0, 0.1, 0),
    new THREE.Vector3(80, 0.1, 10),
    new THREE.Vector3(160, 5, -20),
    new THREE.Vector3(200, 0.1, -80),
    new THREE.Vector3(180, 0.1, -150),
    new THREE.Vector3(120, 0.1, -200),
    new THREE.Vector3(40, 0.1, -220),
    new THREE.Vector3(-30, 0.1, -180),
    new THREE.Vector3(-80, 0.1, -120),
    new THREE.Vector3(-100, 0.1, -50),
    new THREE.Vector3(-90, 0.1, 30),
    new THREE.Vector3(-60, 0.1, 80),
    new THREE.Vector3(0, 0.1, 100)
  ];

  trackCurve = new THREE.CatmullRomCurve3(points, true);

  TRACK_SMOOTH = [];
  for (let i = 0; i < TRACK_SMOOTH_COUNT; i++) {
    TRACK_SMOOTH.push(trackCurve.getPointAt(i / TRACK_SMOOTH_COUNT));
  }

  TRACK_TANGENTS = [];
  TRACK_NORMALS = [];
  for (let i = 0; i < TRACK_SMOOTH.length; i++) {
    const t = i / TRACK_SMOOTH.length;
    const tan = trackCurve.getTangentAt(t);
    TRACK_TANGENTS.push(tan.clone());
    TRACK_NORMALS.push(new THREE.Vector3(-tan.z, 0, tan.x).normalize());
  }
}

function createTrackMesh() {
  // Road surface
  const roadGeo = new THREE.BufferGeometry();
  const vertices = [];
  const uvs = [];

  for (let i = 0; i < TRACK_SMOOTH.length; i++) {
    const t = i / TRACK_SMOOTH.length;
    const pt = TRACK_SMOOTH[i];
    const norm = TRACK_NORMALS[i];
    const halfW = TRACK_WIDTH / 2;

    vertices.push(
      pt.x + norm.x * halfW, pt.y, pt.z + norm.z * halfW,
      pt.x - norm.x * halfW, pt.y, pt.z - norm.z * halfW
    );
    uvs.push(0, t * 50, 1, t * 50);
  }

  const indices = [];
  for (let i = 0; i < TRACK_SMOOTH.length - 1; i++) {
    const a = i * 2, b = i * 2 + 1, c = (i + 1) * 2, d = (i + 1) * 2 + 1;
    indices.push(a, c, b, b, c, d);
  }

  roadGeo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  roadGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  roadGeo.setIndex(indices);
  roadGeo.computeVertexNormals();

  const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
  const road = new THREE.Mesh(roadGeo, roadMat);
  road.receiveShadow = true;
  scene.add(road);

  // Road markings (center line)
  for (let i = 0; i < TRACK_SMOOTH.length - 1; i += 3) {
    const t = i / TRACK_SMOOTH.length;
    const pt = TRACK_SMOOTH[i];
    if (Math.floor(t * 200) % 4 < 2) {
      const markGeo = new THREE.PlaneGeometry(0.3, 3);
      const markMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const mark = new THREE.Mesh(markGeo, markMat);
      mark.rotation.x = -Math.PI / 2;
      mark.position.set(pt.x, pt.y + 0.05, pt.z);
      scene.add(mark);
    }
  }

  // Barriers
  const barrierMat = new THREE.MeshStandardMaterial({ color: 0xff4444 });
  const barrierGeo = new THREE.BoxGeometry(1, 1.2, 3);

  for (let i = 0; i < TRACK_SMOOTH.length; i += 5) {
    const pt = TRACK_SMOOTH[i];
    const norm = TRACK_NORMALS[i];

    [-1, 1].forEach(side => {
      const barrier = new THREE.Mesh(barrierGeo, barrierMat);
      barrier.position.set(
        pt.x + norm.x * (TRACK_WIDTH / 2 + 0.5) * side,
        0.6,
        pt.z + norm.z * (TRACK_WIDTH / 2 + 0.5) * side
      );
      barrier.lookAt(pt.x, 0.6, pt.z);
      barrier.castShadow = true;
      scene.add(barrier);
      barriers.push(barrier);
    });
  }

  // Start/finish line
  const startGeo = new THREE.PlaneGeometry(TRACK_WIDTH, 4);
  const startMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
  const startLine = new THREE.Mesh(startGeo, startMat);
  startLine.rotation.x = -Math.PI / 2;
  startLine.position.set(TRACK_SMOOTH[0].x, 0.15, TRACK_SMOOTH[0].z);
  scene.add(startLine);

  // Checkpoint markers
  for (let i = 0; i < CHECKPOINT_COUNT; i++) {
    const t = (i + 1) / CHECKPOINT_COUNT;
    const pt = trackCurve.getPointAt(t);
    const norm = TRACK_NORMALS[Math.floor(t * TRACK_SMOOTH.length)];

    // Arch over track
    const archGeo = new THREE.BoxGeometry(TRACK_WIDTH + 2, 0.5, 1);
    const archMat = new THREE.MeshStandardMaterial({ color: 0xffff00 });
    const arch = new THREE.Mesh(archGeo, archMat);
    arch.position.set(pt.x, 4, pt.z);
    scene.add(arch);

    // Pillars
    [-1, 1].forEach(side => {
      const pillarGeo = new THREE.CylinderGeometry(0.3, 0.3, 4);
      const pillarMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
      const pillar = new THREE.Mesh(pillarGeo, pillarMat);
      pillar.position.set(
        pt.x + norm.x * (TRACK_WIDTH / 2) * side,
        2,
        pt.z + norm.z * (TRACK_WIDTH / 2) * side
      );
      scene.add(pillar);
    });

    checkpoints.push({ position: pt.clone(), index: i });
  }
}

// ==================== SCENERY GENERATION ====================
function createScenery() {
  // Ground plane
  const groundGeo = new THREE.PlaneGeometry(1000, 1000);
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x2d5a27 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = 0;
  ground.receiveShadow = true;
  scene.add(ground);

  // Trees along track
  const trunkGeo = new THREE.CylinderGeometry(0.5, 0.7, 4);
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
  const leavesGeo = new THREE.SphereGeometry(2.5, 8, 6);
  const leavesMat = new THREE.MeshStandardMaterial({ color: 0x228B22 });

  for (let i = 0; i < TRACK_SMOOTH.length; i += 15) {
    const pt = TRACK_SMOOTH[i];
    const norm = TRACK_NORMALS[i];

    [-1, 1].forEach(side => {
      const dist = TRACK_WIDTH / 2 + 8 + Math.random() * 15;
      const x = pt.x + norm.x * dist * side;
      const z = pt.z + norm.z * dist * side;

      // Trunk
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.set(x, 2, z);
      trunk.castShadow = true;
      scene.add(trunk);

      // Leaves
      const leaves = new THREE.Mesh(leavesGeo, leavesMat);
      leaves.position.set(x, 5 + Math.random() * 2, z);
      leaves.scale.set(0.8 + Math.random() * 0.4, 0.8 + Math.random() * 0.4, 0.8 + Math.random() * 0.4);
      leaves.castShadow = true;
      scene.add(leaves);
    });
  }

  // Mountains in background
  const mountainGeo = new THREE.ConeGeometry(30, 60, 6);
  const mountainMat = new THREE.MeshStandardMaterial({ color: 0x4a4a4a });

  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2;
    const dist = 250 + Math.random() * 100;
    const mountain = new THREE.Mesh(mountainGeo, mountainMat);
    mountain.position.set(Math.cos(angle) * dist, 30, Math.sin(angle) * dist);
    mountain.scale.set(0.8 + Math.random() * 0.5, 0.6 + Math.random() * 0.8, 0.8 + Math.random() * 0.5);
    scene.add(mountain);
  }
}

// ==================== CAR CREATION ====================
function createCarMesh(color, accentColor) {
  const carGroup = new THREE.Group();

  // Main body
  const bodyGeo = new THREE.BoxGeometry(2.2, 0.8, 4.5);
  const bodyMat = new THREE.MeshStandardMaterial({ color: color, metalness: 0.6, roughness: 0.3 });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.position.y = 0.6;
  body.castShadow = true;
  carGroup.add(body);

  // Cabin
  const cabinGeo = new THREE.BoxGeometry(1.8, 0.7, 2);
  const cabinMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8, roughness: 0.2 });
  const cabin = new THREE.Mesh(cabinGeo, cabinMat);
  cabin.position.set(0, 1.35, -0.3);
  cabin.castShadow = true;
  carGroup.add(cabin);

  // Wheels
  const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 12);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

  [[-1.1, 0.4, 1.5], [1.1, 0.4, 1.5], [-1.1, 0.4, -1.5], [1.1, 0.4, -1.5]].forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(...pos);
    wheel.castShadow = true;
    carGroup.add(wheel);
  });

  // Headlights
  const lightGeo = new THREE.SphereGeometry(0.2, 8, 8);
  const lightMat = new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 0.5 });
  [[-0.7, 0.6, 2.3], [0.7, 0.6, 2.3]].forEach(pos => {
    const light = new THREE.Mesh(lightGeo, lightMat);
    light.position.set(...pos);
    carGroup.add(light);
  });

  // Taillights
  const tailLightMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.3 });
  [[-0.7, 0.6, -2.3], [0.7, 0.6, -2.3]].forEach(pos => {
    const tailLight = new THREE.Mesh(lightGeo, tailLightMat);
    tailLight.position.set(...pos);
    carGroup.add(tailLight);
  });

  // Accent stripe
  const stripeGeo = new THREE.BoxGeometry(0.1, 0.1, 4);
  const stripeMat = new THREE.MeshStandardMaterial({ color: accentColor, emissive: accentColor, emissiveIntensity: 0.2 });
  const stripe = new THREE.Mesh(stripeGeo, stripeMat);
  stripe.position.set(0, 0.6, 0);
  carGroup.add(stripe);

  return carGroup;
}

// ==================== CAR DEFINITIONS ====================
const CAR_DEFS = [
  {
    name: "Thunder GT",
    color: 0xff2222,
    accentColor: 0xffaa00,
    maxSpeed: 85,
    acceleration: 32,
    braking: 45,
    handling: 3.2,
    description: "Balanced all-rounder"
  },
  {
    name: "Storm Racer",
    color: 0x2266ff,
    accentColor: 0x00ccff,
    maxSpeed: 95,
    acceleration: 28,
    braking: 40,
    handling: 2.8,
    description: "High speed, less grip"
  },
  {
    name: "Iron Wolf",
    color: 0x22aa44,
    accentColor: 0xffdd00,
    maxSpeed: 75,
    acceleration: 38,
    braking: 50,
    handling: 3.8,
    description: "Quick accel, great handling"
  }
];

// ==================== GAME STATE ====================
let gameState = {
  phase: "menu", // menu, carSelect, countdown, racing, paused, finished
  selectedCarIndex: 0,
  cameraMode: 0, // 0=chase, 1=hood, 2=overhead
  player: null,
  npcs: [],
  countdownTimer: 3,
  raceStartTime: 0,
  currentLap: 1,
  maxLaps: 3,
  checkpointsPassed: new Set(),
  lapTimes: [],
  lapStartTime: 0,
  playerFinished: false,
  finishOrder: [],
  raceTimer: 0,
  keysDown: {},
  lastFrameTime: 0
};

// ==================== INPUT HANDLING ====================
function setupInput() {
  document.addEventListener("keydown", (e) => {
    gameState.keysDown[e.key.toLowerCase()] = true;
    gameState.keysDown[e.code] = true;

    if (gameState.phase === "racing") {
      if (e.key.toLowerCase() === "c") switchCamera();
      if (e.key.toLowerCase() === "p" || e.key === "Escape") togglePause();
      if (e.key.toLowerCase() === "r") restartRace();
    }
  });

  document.addEventListener("keyup", (e) => {
    gameState.keysDown[e.key.toLowerCase()] = false;
    gameState.keysDown[e.code] = false;
  });
}

function switchCamera() {
  gameState.cameraMode = (gameState.cameraMode + 1) % 3;
  updateHUD();
}

function togglePause() {
  if (gameState.phase === "racing") {
    gameState.phase = "paused";
    document.getElementById("pauseScreen").style.display = "flex";
  } else if (gameState.phase === "paused") {
    gameState.phase = "racing";
    gameState.lastFrameTime = performance.now();
    document.getElementById("pauseScreen").style.display = "none";
  }
}

function restartRace() {
  initGame();
}

// ==================== VEHICLE PHYSICS ====================
class Vehicle {
  constructor(def, isPlayer, startPos) {
    this.def = def;
    this.isPlayer = isPlayer;
    this.mesh = createCarMesh(def.color, def.accentColor);
    this.position = startPos.clone();
    this.velocity = new THREE.Vector3(0, 0, 0);
    this.speed = 0;
    this.angle = 0;
    this.lap = 1;
    this.checkpointsPassed = new Set();
    this.finished = false;
    this.finishTime = 0;
    this.lapTimes = [];
    this.lapStartTime = 0;
    this.stuckTimer = 0;
    this.lastPos = startPos.clone();
    this.targetTrackIndex = 0;
    this.npcTargetProgress = 0;
    this.npcSpeedFactor = 0.85 + Math.random() * 0.25;
    this.npcLaneOffset = (Math.random() - 0.5) * (TRACK_WIDTH * 0.4);
    this.collisionCooldown = 0;

    scene.add(this.mesh);
  }

  update(dt, allVehicles) {
    if (this.finished) return;

    // Update collision cooldown
    if (this.collisionCooldown > 0) this.collisionCooldown -= dt;

    let accelInput = 0;
    let brakeInput = 0;
    let steerInput = 0;

    if (this.isPlayer && gameState.phase === "racing") {
      if (gameState.keysDown["w"] || gameState.keysDown["ArrowUp"]) accelInput = 1;
      if (gameState.keysDown["s"] || gameState.keysDown["ArrowDown"]) brakeInput = 1;
      if (gameState.keysDown["a"] || gameState.keysDown["ArrowLeft"]) steerInput = -1;
      if (gameState.keysDown["d"] || gameState.keysDown["ArrowRight"]) steerInput = 1;
    } else if (!this.isPlayer && gameState.phase === "racing") {
      this.updateNPC(dt, allVehicles);
      return;
    }

    // Acceleration
    if (accelInput > 0) {
      this.speed += this.def.acceleration * dt;
    } else if (brakeInput > 0) {
      if (this.speed > 1) {
        this.speed -= this.def.braking * dt;
      } else {
        this.speed -= this.def.acceleration * 0.5 * dt;
      }
    } else {
      // Natural deceleration
      this.speed *= (1 - 1.5 * dt);
    }

    // Clamp speed
    this.speed = Math.max(-this.def.maxSpeed * 0.3, Math.min(this.def.maxSpeed, this.speed));

    // Steering
    const speedFactor = Math.min(Math.abs(this.speed) / 20, 1);
    const steerAmount = steerInput * this.def.handling * speedFactor * dt;
    this.angle += steerAmount * (this.speed > 0 ? 1 : -1);

    // Calculate movement direction
    const moveDir = new THREE.Vector3(Math.sin(this.angle), 0, Math.cos(this.angle));
    const targetVelocity = moveDir.multiplyScalar(this.speed);

    // Smooth velocity transition
    this.velocity.lerp(targetVelocity, Math.min(dt * 5, 1));

    // Store last position for collision detection
    this.lastPos.copy(this.position);

    // Apply movement
    this.position.add(this.velocity.clone().multiplyScalar(dt));

    // Update mesh position and rotation
    this.mesh.position.copy(this.position);
    this.mesh.rotation.y = this.angle;

    // Track boundary collision
    this.checkTrackBoundaries();

    // Vehicle-vehicle collision
    this.checkVehicleCollisions(allVehicles);

    // Check if stuck
    const distMoved = this.position.distanceTo(this.lastPos);
    if (distMoved < 0.1 && Math.abs(this.speed) > 5) {
      this.stuckTimer += dt;
      if (this.stuckTimer > 2) {
        // Push forward to unstuck
        const pushDir = new THREE.Vector3(Math.sin(this.angle), 0, Math.cos(this.angle));
        this.position.add(pushDir.multiplyScalar(2));
        this.speed *= 0.5;
        this.stuckTimer = 0;
      }
    } else {
      this.stuckTimer = 0;
    }

    // Update lap tracking for player
    if (this.isPlayer) {
      this.checkLapProgress();
    }
  }
