import * as THREE from 'three';

// --- Constants & Config ---
const TOTAL_LAPS = 3;
const TRACK_WIDTH = 18;
const NUM_NPCS = 4;
const CHECKPOINT_COUNT = 4;

const CAR_DEFS = [
  { name: 'Thunder', color: 0xff2222, accentColor: 0xcc0000, maxSpeed: 95, acceleration: 38, braking: 45, handling: 3.2 },
  { name: 'Viper', color: 0x22aa22, accentColor: 0x118811, maxSpeed: 85, acceleration: 45, braking: 40, handling: 3.8 },
  { name: 'Phantom', color: 0x2266ff, accentColor: 0x1144cc, maxSpeed: 105, acceleration: 30, braking: 38, handling: 2.8 }
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

// --- Global State ---
let scene, camera, renderer, clock;
let playerCar = null, npcCars = [];
let trackCurve, TRACK_SMOOTH = [], TRACK_NORMALS = [];
let gameState = 'menu'; 
let selectedCarIndex = 0;
let currentCameraMode = 0;
const cameraModes = ['Chase', 'Cockpit', 'Overhead'];
let raceTimer = 0, lapTimes = [], currentLap = 1;
let lastCheckpointIndex = -1, countdownValue = 3, countdownTimer = 0;
let keys = {}, trackMesh, barrierMeshes = [];
let startLineMesh, minimapCtx, playerFinishTime = null, npcFinishTimes = [];
let racePositions = [];

// --- Initialization ---
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
  if (mc) { mc.width = 180; mc.height = 180; minimapCtx = mc.getContext('2d'); }

  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', onKeyUp);
  window.addEventListener('resize', onResize);

  buildCarSelectUI();
  updateUIState('menu');
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
  const segs = 600; TRACK_SMOOTH = []; TRACK_NORMALS = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs;
    const pt = trackCurve.getPointAt(t);
    const tan = trackCurve.getTangentAt(t);
    TRACK_SMOOTH.push(pt);
    TRACK_NORMALS.push(new THREE.Vector3(-tan.z, 0, tan.x).normalize());
  }

  // Road surface
  const verts = [], idxs = [], norms = [];
  for (let i = 0; i <= segs; i++) {
    const t = i / segs, pt = trackCurve.getPointAt(t);
    const norm = TRACK_NORMALS[i];
    const L = pt.clone().add(norm.clone().multiplyScalar(TRACK_WIDTH / 2));
    const R = pt.clone().sub(norm.clone().multiplyScalar(TRACK_WIDTH / 2));
    verts.push(L.x, 0.01, L.z, R.x, 0.01, R.z);
    norms.push(0,1,0, 0,1,0);
    if (i < segs) {
      const base = i * 2;
      idxs.push(base, base+1, base+2, base+1, base+3, base+2);
    }
  }
  const roadGeo = new THREE.BufferGeometry();
  roadGeo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
  roadGeo.setAttribute('normal', new THREE.Float32BufferAttribute(norms, 3));
  roadGeo.setIndex(idxs);
  const roadMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.8 });
  trackMesh = new THREE.Mesh(roadGeo, roadMat);
  trackMesh.receiveShadow = true;
  scene.add(trackMesh);

  // Barriers
  barrierMeshes = [];
  for (let side = -1; side <= 1; side += 2) {
    const bVerts = [], bIdxs = [], bNorms = [];
    for (let i = 0; i <= segs; i++) {
      const t = i / segs, pt = trackCurve.getPointAt(t);
      const norm = TRACK_NORMALS[i];
      const offset = side * (TRACK_WIDTH / 2 + 1.5);
      const L = pt.clone().add(norm.clone().multiplyScalar(offset));
      const R = L.clone(); R.y += 3;
      bVerts.push(L.x, L.y, L.z, R.x, R.y, R.z);
      bNorms.push(0,1,0, 0,1,0);
      if (i < segs) {
        const base = i * 2;
        bIdxs.push(base, base+1, base+2, base+1, base+3, base+2);
      }
    }
    const bGeo = new THREE.BufferGeometry();
    bGeo.setAttribute('position', new THREE.Float32BufferAttribute(bVerts, 3));
    bGeo.setAttribute('normal', new THREE.Float32BufferAttribute(bNorms, 3));
    bGeo.setIndex(bIdxs);
    const bMat = new THREE.MeshStandardMaterial({ color: side === -1 ? 0xff0000 : 0xffffff });
    const barrier = new THREE.Mesh(bGeo, bMat);
    barrier.castShadow = true;
    scene.add(barrier);
    barrierMeshes.push(barrier);
  }

  // Start/Finish Line
  const startPt = TRACK_SMOOTH[0];
  const startTan = trackCurve.getTangentAt(0);
  const startNorm = new THREE.Vector3(-startTan.z, 0, startTan.x).normalize();
  const lineGeo = new THREE.PlaneGeometry(TRACK_WIDTH, 2);
  const lineMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
  startLineMesh = new THREE.Mesh(lineGeo, lineMat);
  startLineMesh.rotation.x = -Math.PI / 2;
  startLineMesh.position.copy(startPt).add(new THREE.Vector3(0, 0.05, 0));
  scene.add(startLineMesh);
}

function buildScenery() {
  const treeGeo = new THREE.ConeGeometry(4, 12, 8);
  const trunkGeo = new THREE.CylinderGeometry(1, 1, 4, 8);
  const treeMat = new THREE.MeshStandardMaterial({ color: 0x228822 });
  const trunkMat = new THREE.MeshStandardMaterial({ color: 0x8B4513 });

  for (let i = 0; i < 100; i++) {
    const t = Math.random();
    const pt = trackCurve.getPointAt(t);
    const norm = TRACK_NORMALS[Math.floor(t * (TRACK_SMOOTH.length - 1))];
    const dist = TRACK_WIDTH / 2 + 15 + Math.random() * 40;
    const side = Math.random() > 0.5 ? 1 : -1;
    const pos = pt.clone().add(norm.clone().multiplyScalar(dist * side));
    pos.y = 0;

    const treeGroup = new THREE.Group();
    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    trunk.position.y = 2; trunk.castShadow = true;
    const leaves = new THREE.Mesh(treeGeo, treeMat);
    leaves.position.y = 8; leaves.castShadow = true;
    treeGroup.add(trunk, leaves);
    treeGroup.position.copy(pos);
    scene.add(treeGroup);
  }

  const mtnGeo = new THREE.ConeGeometry(60, 150, 8);
  const mtnMat = new THREE.MeshStandardMaterial({ color: 0x555577 });
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2;
    const r = 300;
    const mtn = new THREE.Mesh(mtnGeo, mtnMat);
    mtn.position.set(Math.cos(angle) * r, 50, Math.sin(angle) * r);
    scene.add(mtn);
  }
}
