import * as THREE from 'three';

const TOTAL_LAPS = 3;
const TRACK_WIDTH = 18;
const NUM_NPCS = 4;

const CAR_DEFS = [
  { name: 'Thunder', color: 0xff2222, accentColor: 0xcc0000, maxSpeed: 95, acceleration: 38, braking: 45, handling: 3.2, description: 'Balanced all-rounder' },
  { name: 'Viper', color: 0x22aa22, accentColor: 0x118811, maxSpeed: 85, acceleration: 45, braking: 40, handling: 3.8, description: 'Quick acceleration' },
  { name: 'Phantom', color: 0x2266ff, accentColor: 0x1144cc, maxSpeed: 105, acceleration: 30, braking: 38, handling: 2.8, description: 'Top speed specialist' }
];

const TRACK_POINTS = [
  new THREE.Vector3(0, 0, -120), new THREE.Vector3(60, 0, -140),
  new THREE.Vector3(130, 0, -100), new THREE.Vector3(170, 0, -30),
  new THREE.Vector3(180, 0, 50), new THREE.Vector3(160, 0, 120),
  new THREE.Vector3(100, 0, 170), new THREE.Vector3(20, 0, 190),
  new THREE.Vector3(-50, 0, 180), new THREE.Vector3(-110, 0, 140),
  new THREE.Vector3(-150, 0, 70), new THREE.Vector3(-160, 0, -10),
  new THREE.Vector3(-140, 0, -80), new THREE.Vector3(-90, 0, -130),
];

let scene, camera, renderer, clock;
let playerCar = null, npcCars = [];
let trackCurve, TRACK_SMOOTH = [];
let gameState = 'menu';
let selectedCarIndex = 0;
let currentCameraMode = 0;
const cameraModes = ['Chase', 'Cockpit', 'Overhead'];
let raceTimer = 0, lapTimes = [], currentLap = 1;
let lastCheckpointIndex = -1, countdownValue = 3, countdownTimer = 0;
let keys = {}, trackMesh, barrierMeshes = [];
let startLineMesh, minimapCtx, playerFinishTime = null, npcFinishTimes = [];

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x87CEEB);
  scene.fog = new THREE.FogExp2(0x87CEEB, 0.0015);
  camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.5, 2000);
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.getElementById('app').appendChild(renderer.domElement);
  clock = new THREE.Clock();
  setupLighting();
  buildTrack();
  buildScenery();
  const mc = document.getElementById('minimap');
  mc.width = 180; mc.height = 180;
  minimapCtx = mc.getContext('2d');
  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', onKeyUp);
  window.addEventListener('resize', onResize);
  buildCarSelectUI();
  animate();
}

function setupLighting() {
  scene.add(new THREE.AmbientLight(0x6688aa, 0.6));
  scene.add(new THREE.HemisphereLight(0x87CEEB, 0x445522, 0.5));
  const sun = new THREE.DirectionalLight(0xffeedd, 1.2);
  sun.position.set(100, 150, 80);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 1; sun.shadow.camera.far = 500;
  sun.shadow.camera.left = -200; sun.shadow.camera.right = 200;
  sun.shadow.camera.top = 200; sun.shadow.camera.bottom = -200;
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0x4466aa, 0.3);
  fill.position.set(-80, 50, -60); scene.add(fill);
}

function buildTrack() {
  const pts = TRACK_POINTS.map(p => p.clone());
  pts.push(pts[0].clone());
  trackCurve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.5);
  const segs = 600; TRACK_SMOOTH = [];
  for (let i = 0; i <= segs; i++) TRACK_SMOOTH.push(trackCurve.getPointAt(i / segs));

  // Road surface
  const verts = [], idxs = [], norms = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs, pt = trackCurve.getPointAt(t);
    const tan = trackCurve.getTangentAt(t);
    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
    const L = pt.clone().add(norm.clone().multiplyScalar(TRACK_WIDTH / 2));
    const R = pt.clone().sub(norm.clone().multiplyScalar(TRACK_WIDTH / 2));
    verts.push(L.x, 0.01, L.z, R.x, 0.01, R.z);
    norms.push(0,1,0, 0,1,0);
    if (i < segs) {
      const base = i * 2;
      idxs.push(base, base+1, base+2, base+1, base+3, base+2);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(norms, 3));
  geo.setIndex(idxs);
  const mat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
  trackMesh = new THREE.Mesh(geo, mat);
  trackMesh.receiveShadow = true;
  scene.add(trackMesh);

  // Barriers
  barrierMeshes = [];
  for (let i = 0; i <= segs; i += 10) {
    const t = i / segs, pt = trackCurve.getPointAt(t);
    const tan = trackCurve.getTangentAt(t);
    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
    [-1, 1].forEach(side => {
      const pos = pt.clone().add(norm.clone().multiplyScalar((TRACK_WIDTH / 2 + 1.5) * side));
      const geo = new THREE.BoxGeometry(3, 1.5, 1);
      const mat = new THREE.MeshStandardMaterial({ color: side === -1 ? 0xff0000 : 0xffffff });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.copy(pos);
      mesh.lookAt(pt);
      mesh.castShadow = true;
      scene.add(mesh);
      barrierMeshes.push(mesh);
    });
  }

  // Start line
  const startPt = trackCurve.getPointAt(0);
  const startTan = trackCurve.getTangentAt(0);
  const startNorm = new THREE.Vector3(-startTan.z, 0, startTan.x).normalize();
  const slGeo = new THREE.PlaneGeometry(TRACK_WIDTH, 2);
  const slMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
  startLineMesh = new THREE.Mesh(slGeo, slMat);
  startLineMesh.rotation.x = -Math.PI / 2;
  startLineMesh.position.copy(startPt);
  startLineMesh.position.y = 0.02;
  scene.add(startLineMesh);
}

function buildScenery() {
  // Ground plane
  const groundGeo = new THREE.PlaneGeometry(800, 800);
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x4a7c3f });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.1;
  ground.receiveShadow = true;
  scene.add(ground);

  // Trees along track
  for (let i = 0; i < TRACK_SMOOTH.length; i += 8) {
    const pt = TRACK_SMOOTH[i];
    const tan = trackCurve.getTangentAt(i / TRACK_SMOOTH.length);
    const norm = new THREE.Vector3(-tan.z, 0, tan.x).normalize();
    [-1, 1].forEach(side => {
      if (Math.random() > 0.4) return;
      const pos = pt.clone().add(norm.clone().multiplyScalar((TRACK_WIDTH / 2 + 8 + Math.random() * 15) * side));
      const treeGroup = new THREE.Group();
      const trunkGeo = new THREE.CylinderGeometry(0.4, 0.6, 3, 6);
      const trunkMat = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.y = 1.5;
      trunk.castShadow = true;
      treeGroup.add(trunk);
      const leavesGeo = new THREE.SphereGeometry(2.5, 6, 4);
      const leavesMat = new THREE.MeshStandardMaterial({ color: 0x2d5a1e });
      const leaves = new THREE.Mesh(leavesGeo, leavesMat);
      leaves.position.y = 4;
      leaves.castShadow = true;
      treeGroup.add(leaves);
      treeGroup.position.copy(pos);
      scene.add(treeGroup);
    });
  }

  // Mountains in background
  for (let i = 0; i < 20; i++) {
    const angle = (i / 20) * Math.PI * 2;
    const dist = 350 + Math.random() * 100;
    const mGeo = new THREE.ConeGeometry(30 + Math.random() * 40, 60 + Math.random() * 80, 7);
    const mMat = new THREE.MeshStandardMaterial({ color: 0x5a5a5a });
    const mountain = new THREE.Mesh(mGeo, mMat);
    mountain.position.set(Math.cos(angle) * dist, 20, Math.sin(angle) * dist);
    scene.add(mountain);
  }
}

function createCarMesh(color, accentColor) {
  const group = new THREE.Group();
  // Body
  const bodyGeo = new THREE.BoxGeometry(2.2, 0.8, 4.5);
  const bodyMat = new THREE.MeshStandardMaterial({ color: color, metalness: 0.6, roughness: 0.3 });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.position.y = 0.6;
  body.castShadow = true;
  group.add(body);
  // Cabin
  const cabinGeo = new THREE.BoxGeometry(1.8, 0.7, 2);
  const cabinMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.8, roughness: 0.2 });
  const cabin = new THREE.Mesh(cabinGeo, cabinMat);
  cabin.position.set(0, 1.25, -0.3);
  cabin.castShadow = true;
  group.add(cabin);
  // Wheels
  const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 8);
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
  [[-1.1, 0.4, 1.5], [1.1, 0.4, 1.5], [-1.1, 0.4, -1.5], [1.1, 0.4, -1.5]].forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(...pos);
    wheel.castShadow = true;
    group.add(wheel);
  });
  // Headlights
  const hlGeo = new THREE.SphereGeometry(0.15, 6, 4);
  const hlMat = new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 0.5 });
  [[-0.7, 0.6, 2.3], [0.7, 0.6, 2.3]].forEach(pos => {
    const hl = new THREE.Mesh(hlGeo, hlMat);
    hl.position.set(...pos);
    group.add(hl);
  });
  // Taillights
  const tlMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.3 });
  [[-0.7, 0.6, -2.3], [0.7, 0.6, -2.3]].forEach(pos => {
    const tl = new THREE.Mesh(hlGeo, tlMat);
    tl.position.set(...pos);
    group.add(tl);
  });
  return group;
}

function buildCarSelectUI() {
  const container = document.getElementById('car-select');
  container.innerHTML = '<h1>🏁 TURBO RACER 🏁</h1><h2>Select Your Vehicle</h2>';
  CAR_DEFS.forEach((car, i) => {
    const div = document.createElement('div');
    div.className = 'car-option';
    div.style.cssText = `border: 3px solid ${i === selectedCarIndex ? '#ffff00' : '#555'}; padding: 15px; margin: 10px; cursor: pointer; border-radius: 8px; background: #222; color: white;`;
    div.innerHTML = `<h3 style="color: #${car.color.toString(16).padStart(6, '0')}">${car.name}</h3><p>${car.description}</p><div class="stats"><span>Speed: ${"█".repeat(Math.floor(car.maxSpeed / 15))}${"░".repeat(7 - Math.floor(car.maxSpeed / 15))}</span><br><span>Accel: ${"█".repeat(Math.floor(car.acceleration / 10))}${"░".repeat(5 - Math.floor(car.acceleration / 10))}</span><br><span>Handling: ${"█".repeat(Math.floor(car.handling / 1))}${"░".repeat(4 - Math.floor(car.handling / 1))}</span></div>`;
    div.onclick = () => { selectedCarIndex = i; buildCarSelectUI(); };
    container.appendChild(div);
  });
  const startBtn = document.createElement('button');
  startBtn.textContent = 'START RACE';
  startBtn.style.cssText = 'padding: 15px 40px; font-size: 20px; background: #ff6600; color: white; border: none; cursor: pointer; margin-top: 20px; border-radius: 8px;';
  startBtn.onclick = () => { gameState = 'countdown'; countdownValue = 3; countdownTimer = 0; document.getElementById('car-select').style.display = 'none'; document.getElementById('hud').style.display = 'block'; startRace(); };
  container.appendChild(startBtn);
}

function startRace() {
  const def = CAR_DEFS[selectedCarIndex];
  playerCar = createCar(def, true);
  npcCars = [];
  for (let i = 0; i < NUM_NPCS; i++) {
    const npcDef = CAR_DEFS[(selectedCarIndex + i + 1) % CAR_DEFS.length];
    npcCars.push(createCar(npcDef, false));
  }
  resetPositions();
}

function createCar(def, isPlayer) {
  const mesh = createCarMesh(def.color, def.accentColor);
  scene.add(mesh);
  return { mesh, def, isPlayer, speed: 0, angle: 0, x: 0, z: 0, lap: 1, checkpointIndex: 0, finished: false, finishTime: 0, trackProgress: 0, prevCheckpointIndex: -1 };
}

function resetPositions() {
  const startPt = TRACK_SMOOTH[0];
  const startTan = trackCurve.getTangentAt(0);
  const startNorm = new THREE.Vector3(-startTan.z, 0, startTan.x).normalize();
  playerCar.x = startPt.x; playerCar.z = startPt.z;
  playerCar.angle = Math.atan2(startTan.x, startTan.z);
  playerCar.speed = 0; playerCar.lap = 1; playerCar.checkpointIndex = 0;
  playerCar.prevCheckpointIndex = -1; playerCar.finished = false;
  npcCars.forEach((npc, i) => {
    const offset = (i + 1) * 8;
    const backPt = trackCurve.getPointAt(1 - offset / TRACK_SMOOTH.length);
    const backTan = trackCurve.getTangentAt(1 - offset / TRACK_SMOOTH.length);
    npc.x = backPt.x; npc.z = backPt.z;
    npc.angle = Math.atan2(backTan.x, backTan.z);
    npc.speed = 0; npc.lap = 1; npc.checkpointIndex = 0;
    npc.prevCheckpointIndex = -1; npc.finished = false; npc.finishTime = 0;
    npc.trackProgress = 1 - offset / TRACK_SMOOTH.length;
  });
}
