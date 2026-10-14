function createCars() {
  const playerSpec = carSpecs[gameState.selectedCarIndex];
  playerCar = createCarMesh(playerSpec);
  playerCar.spec = playerSpec; playerCar.finished = false; playerCar.checkpointIndex = -1;
  playerCar.velocity = new THREE.Vector3(0, 0, 0); playerCar.acceleration = 0;
  playerCar.steeringAngle = 0; playerCar.position.set(config.trackRadius, 2, 0);
  gameState.cars.push(playerCar); allCars.push(playerCar);
  for (let i = 0; i < config.npcCount; i++) {
    const npcSpec = carSpecs[i % carSpecs.length];
    npcSpec.name = npcSpec.name + ' ' + (i + 1);
    const npcCar = createCarMesh(npcSpec);
    npcCar.spec = npcSpec; npcCar.finished = false; npcCar.checkpointIndex = -1;
    npcCar.velocity = new THREE.Vector3(0, 0, 15); npcCar.acceleration = 0; npcCar.steeringAngle = 0;
    const angle = (i / config.npcCount) * Math.PI * 2 + 0.5;
    npcCar.position.set(config.trackRadius + Math.cos(angle) * 148, 2, Math.sin(angle) * 148);
    gameState.npcCars.push(npcCar); allCars.push(npcCar);
  }
}

function createCarMesh(spec) {
  const carGroup = new THREE.Group();
  const bodyGeometry = new THREE.BoxGeometry(2, 1, 4);
  const bodyMaterial = new THREE.MeshLambertMaterial({ color: spec.color });
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial); body.position.y = 0.5; carGroup.add(body);
  const cabinGeometry = new THREE.BoxGeometry(1.8, 0.7, 2);
  const cabinMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
  const cabin = new THREE.Mesh(cabinGeometry, cabinMaterial); cabin.position.set(0, 1.2, -0.5); carGroup.add(cabin);
  const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
  const wheelMaterial = new THREE.MeshLambertMaterial({ color: 0x111111 });
  const positions = [{ x: -1, z: 1.2 }, { x: 1, z: 1.2 }, { x: -1, z: -1.2 }, { x: 1, z: -1.2 }];
  positions.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial); wheel.rotation.z = Math.PI / 2;
    wheel.position.set(pos.x, 0.4, pos.z); carGroup.add(wheel);
  });
  return carGroup;
}

function setupInput() {
  window.addEventListener('keydown', (e) => {
    keys[e.code] = true;
    if (gameState.screen === 'race') {
      if (e.code === 'KeyC') gameState.cameraMode = (gameState.cameraMode + 1) % 3;
      if ((e.code === 'KeyP' || e.code === 'Escape')) gameState.isPaused = !gameState.isPaused;
      if (e.code === 'KeyR') location.reload();
    }
  });
  window.addEventListener('keyup', (e) => keys[e.code] = false);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  if (gameState.screen === 'race' && !gameState.isPaused) {
    const dt = Math.min(clock.getDelta(), 0.1);
    updateGame(dt);
  }
  renderer.render(scene, camera);
}

function updateGame(dt) {
  if (playerCar) updateCar(playerCar, dt, { up: keys.w || keys.ArrowUp, down: keys.s || keys.ArrowDown,
    left: keys.a || keys.ArrowLeft, right: keys.d || keys.ArrowRight });
  updateNPCs(dt); checkCollisions(); updateCamera(); checkLapCompletion();
}

function updateCar(car, dt, input) {
  const spec = car.spec;
  if (input.up) car.velocity.z += spec.acceleration * dt;
  if (input.down) car.velocity.z -= spec.braking * dt;
  const maxSpeed = spec.maxSpeed / 3.6; const currentSpeed = car.velocity.length();
  if (currentSpeed > maxSpeed) car.velocity.normalize().multiplyScalar(maxSpeed);
  car.velocity.multiplyScalar(0.995);
  const currentAngle = Math.atan2(car.velocity.x, car.velocity.z);
  let targetAngle = currentAngle;
  if (input.left) targetAngle -= spec.handling * dt;
  if (input.right) targetAngle += spec.handling * dt;
  const angleDiff = targetAngle - currentAngle;
  car.steeringAngle += angleDiff * 0.1;
  const steerFactor = Math.min(Math.abs(car.velocity.z) / maxSpeed, 1);
  car.velocity.x -= Math.sin(angleDiff) * steerFactor * spec.handling * dt;
}

function updateNPCs(dt) {
  gameState.npcCars.forEach(npc => {
    const spec = npc.spec; const maxSpeed = spec.maxSpeed / 3.6;
    const targetAngle = Math.atan2(npc.position.z, npc.position.x);
    const currentAngle = Math.atan2(npc.velocity.x, npc.velocity.z);
    const angleDiff = targetAngle - currentAngle;
    npc.velocity.x -= Math.sin(angleDiff) * 0.5 * dt;
    npc.velocity.y = 0;
    if (npc.velocity.length() < maxSpeed) npc.velocity.normalize().multiplyScalar(maxSpeed * 0.98);
    npc.position.add(npc.velocity.clone().multiplyScalar(dt));
  });
}

function checkCollisions() {
  for (let i = 0; i < allCars.length; i++) {
    for (let j = i + 1; j < allCars.length; j++) {
      const car1 = allCars[i], car2 = allCars[j];
      const distSq = car1.position.distanceToSquared(car2.position);
      if (distSq < 4) {
        const pushDir = car2.position.clone().sub(car1.position).normalize();
        car1.velocity.add(pushDir.multiplyScalar(0.5));
        car2.velocity.sub(pushDir.multiplyScalar(0.5));
      }
    }
  }
}

function updateCamera() {
  const playerPos = playerCar ? playerCar.position.clone() : new THREE.Vector3(0, 0, 0);
  if (gameState.cameraMode === 0) { // Chase
    camera.position.set(playerPos.x + Math.sin(playerCar.steeringAngle || 0) * 15, 8, playerPos.z + Math.cos(playerCar.steeringAngle || 0) * 15);
    camera.lookAt(playerPos.x, 2, playerPos.z);
  } else if (gameState.cameraMode === 1) { // Hood
    camera.position.set(playerPos.x + Math.sin(playerCar.steeringAngle || 0) * 3, 0.8, playerPos.z + Math.cos(playerCar.steeringAngle || 0) * 3);
    camera.lookAt(playerPos.x, 2, playerPos.z);
  } else { // Overhead
    camera.position.set(playerPos.x + Math.sin(playerCar.steeringAngle || 0) * 40, 60, playerPos.z + Math.cos(playerCar.steeringAngle || 0) * 40);
    camera.lookAt(playerPos.x, 2, playerPos.z);
  }
}

function checkLapCompletion() {
  const startPos = { x: config.trackRadius, z: 0 };
  allCars.forEach(car => {
    if (!car.finished) {
      const distToStart = Math.sqrt((car.position.x - startPos.x)**2 + (car.position.z - startPos.z)**2);
      if (distToStart < 10 && car.checkpointIndex === gameState.checkpoints.length - 1) {
        car.finished = true;
        gameState.lapsCompleted++;
        if (gameState.lapsCompleted >= config.totalLaps) showResults();
      }
    }
  });
}

function showResults() {
  const allCarsList = [...gameState.cars, ...gameState.npcCars].filter(c => !c.finished);
  if (allCarsList.length === 0) {
    document.getElementById('app').innerHTML = '<div class="menu-container"><h1>🏁 Race Complete!</h1><h2>Final Standings</h2><ol id="standings"></ol><button onclick="restartRace()">Play Again</button></div>';
    const standings = allCarsList.map((car, i) => '<li>' + (i + 1) + '. ' + car.spec.name + ' - Finished</li>').join('');
    document.getElementById('standings').innerHTML = standings;
  }
}

function restartRace() {
  location.reload();
}

function showMenu() {
  gameState.screen = 'menu';
  const carCards = carSpecs.map((spec, i) => '<div class="car-card" onclick="selectCar(' + i + ')"><h3>' + spec.name + '</h3><p>Speed: ' + spec.maxSpeed + ' km/h</p><p>Acceleration: ' + spec.acceleration + '</p><p>Braking: ' + spec.braking + '</p><p style="color:' + spec.color + '">Color: ' + spec.color.toString(16) + '</p></div>').join('');
  document.getElementById('app').innerHTML = '<div class="menu-container"><h1>🏎️ Arcade Racing</h1><p>Select your car:</p><div class="car-selection">' + carCards + '</div><p class="controls">W/↑: Accelerate | S/↓: Brake | A/←: Left | D/→: Right<br>C: Camera | P: Pause | R: Restart</p></div>';
}

function selectCar(index) {
  gameState.selectedCarIndex = index;
  init();
}

function startRace() {
  gameState.screen = 'race';
  gameState.countdown = 3;
  gameState.lapsCompleted = 0;
  playerCar.position.set(config.trackRadius, 2, 0);
  allCars.forEach(car => {
    car.velocity.set(0, 0, 0);
    car.checkpointIndex = -1;
  });
}

function showHUD() {
  const hud = document.createElement('div');
  hud.id = 'hud';
  hud.innerHTML = '<div class="hud-top"><span>Lap: ' + (gameState.lapsCompleted + 1) + '/' + config.totalLaps + '</span><span>Position: ' + getRacePosition() + '</span></div>';
  document.body.appendChild(hud);
}

function getRacePosition() {
  const sorted = [...allCars].sort((a, b) => a.position.distanceTo(config.trackRadius, 0, 0) - b.position.distanceTo(config.trackRadius, 0, 0));
  return allCars.indexOf(playerCar) + 1;
}

function showCountdown() {
  const countdownEl = document.getElementById('countdown');
  if (countdownEl) countdownEl.textContent = gameState.countdown;
  if (gameState.countdown > 0) {
    gameState.countdown--;
    setTimeout(showCountdown, 1000);
  } else {
    startRace();
  }
}

function showResultsScreen() {
  const allCarsList = [...gameState.cars, ...gameState.npcCars].filter(c => !c.finished);
  if (allCarsList.length === 0) {
    document.getElementById('app').innerHTML = '<div class="menu-container"><h1>🏁 Race Complete!</h1><h2>Final Standings</h2><ol id="standings"></ol><button onclick="restartRace()">Play Again</button></div>';
    const standings = allCarsList.map((car, i) => '<li>' + (i + 1) + '. ' + car.spec.name + ' - Finished</li>').join('');
    document.getElementById('standings').innerHTML = standings;
  }
}

function restartRace() {
  location.reload();
}

// Initialize on load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    init();
    showMenu();
  });
} else {
  init();
  showMenu();
}
