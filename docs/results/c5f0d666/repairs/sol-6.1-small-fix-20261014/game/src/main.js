import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Track } from './Track.js';
import { Car } from './Car.js';
import { NPC } from './NPC.js';

// Create scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);

// Create camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 10, 20);

// Create renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;

// Add renderer to DOM
document.body.appendChild(renderer.domElement);

// Create track
const track = new Track();
track.getTrackSegments().forEach(segment => scene.add(segment));
track.getCheckpoints().forEach(checkpoint => scene.add(checkpoint));
scene.add(track.getStartFinishLine());

// Create cars
const car = new Car({
  maxSpeed: 10,
  accelerationRate: 2,
  brakeForce: 3,
  handling: 0.8
});
scene.add(car.getCar());

// Create NPCs
const npcs = [];
for (let i = 0; i < 4; i++) {
  const npc = new NPC(track, {
    maxSpeed: 8 + Math.random() * 2,
    accelerationRate: 1.5 + Math.random() * 0.5,
    brakeForce: 2.5 + Math.random() * 0.5,
    handling: 0.7 + Math.random() * 0.2
  });
  npcs.push(npc);
  scene.add(npc.getCar());
}

// Create lights
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(1, 1, 1).normalize();
scene.add(light);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

// Create controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;

// Create variables for game state
let gameStarted = false;
let gamePaused = false;
let currentCamera = 'chase';

// Create variables for input handling
const keys = {};

// Add event listeners for keyboard input
window.addEventListener('keydown', (event) => {
  keys[event.key] = true;
});

window.addEventListener('keyup', (event) => {
  keys[event.key] = false;
});

// Add event listener for window resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// Create function to update game state
function update() {
  // Update game state
  if (gameStarted && !gamePaused) {
    // Update car
    car.update(1/60);
    
    // Update NPCs
    npcs.forEach(npc => {
      npc.update(1/60);
    });
    
    // Update camera
    updateCamera();
    
    // Update controls
    controls.update();
    
    // Update renderer
    renderer.render(scene, camera);
  }
}

// Create function to update camera
function updateCamera() {
  // Update camera based on current camera mode
  if (currentCamera === 'chase') {
    // Update chase camera
    camera.position.x = car.getCar().position.x + 5;
    camera.position.y = 10;
    camera.position.z = car.getCar().position.z + 5;
    camera.lookAt(car.getCar().position);
  } else if (currentCamera === 'hood') {
    // Update hood camera
    camera.position.x = car.getCar().position.x;
    camera.position.y = 5;
    camera.position.z = car.getCar().position.z + 5;
    camera.lookAt(car.getCar().position);
  } else if (currentCamera === 'overhead') {
    // Update overhead camera
    camera.position.x = 0;
    camera.position.y = 50;
    camera.position.z = 0;
    camera.lookAt(car.getCar().position);
  }
}

// Create function to start game
function startGame() {
  // Set game started flag
  gameStarted = true;
}

// Create function to pause game
function pauseGame() {
  // Toggle game paused flag
  gamePaused = !gamePaused;
}

// Create function to restart game
function restartGame() {
  // Reset game state
  gameStarted = false;
  gamePaused = false;
  currentCamera = 'chase';
  
  // Reset car
  car.setPosition(new THREE.Vector3(0, 0, 0));
  car.setMoving(false);
  car.setBraking(false);
  car.setReversing(false);
  car.setAcceleration(0);
  car.setMaxSpeed(10);
  car.setAccelerationRate(2);
  car.setBrakeForce(3);
  car.setHandling(0.8);
  
  // Reset NPCs
  npcs.forEach(npc => {
    npc.setPosition(new THREE.Vector3(0, 0, 0));
    npc.setMoving(false);
    npc.setBraking(false);
    npc.setReversing(false);
    npc.setAcceleration(0);
    npc.setMaxSpeed(8 + Math.random() * 2);
    npc.setAccelerationRate(1.5 + Math.random() * 0.5);
    npc.setBrakeForce(2.5 + Math.random() * 0.5);
    npc.setHandling(0.7 + Math.random() * 0.2);
  });
}

// Create function to change camera
function changeCamera() {
  // Toggle camera mode
  if (currentCamera === 'chase') {
    currentCamera = 'hood';
  } else if (currentCamera === 'hood') {
    currentCamera = 'overhead';
  } else if (currentCamera === 'overhead') {
    currentCamera = 'chase';
  }
}

// Create function to handle input
function handleInput() {
  // Handle input based on current game state
  if (gameStarted && !gamePaused) {
    // Handle acceleration
    if (keys['w'] || keys['ArrowUp']) {
      car.setMoving(true);
      car.setBraking(false);
      car.setReversing(false);
    } else if (keys['s'] || keys['ArrowDown']) {
      car.setMoving(false);
      car.setBraking(false);
      car.setReversing(true);
    } else {
      car.setMoving(false);
      car.setBraking(true);
      car.setReversing(false);
    }
    
    // Handle steering
    if (keys['a'] || keys['ArrowLeft']) {
      car.setAcceleration(-1);
    } else if (keys['d'] || keys['ArrowRight']) {
      car.setAcceleration(1);
    } else {
      car.setAcceleration(0);
    }
    
    // Handle camera change
    if (keys['c']) {
      changeCamera();
      keys['c'] = false;
    }
    
    // Handle pause
    if (keys['p'] || keys['Escape']) {
      pauseGame();
      keys['p'] = false;
      keys['Escape'] = false;
    }
    
    // Handle restart
    if (keys['r']) {
      restartGame();
      keys['r'] = false;
    }
  }
}

// Create function to render game
function render() {
  // Update game state
  update();
  
  // Handle input
  handleInput();
  
  // Render scene
  renderer.render(scene, camera);
}

// Create function to animate game
function animate() {
  // Request next frame
  requestAnimationFrame(animate);
  
  // Render game
  render();
}

// Start animation
animate();

// Start game
startGame();