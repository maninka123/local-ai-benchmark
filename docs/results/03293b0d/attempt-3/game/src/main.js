    this.opponentCars.forEach((car, i) => {
      car.position.set(-20 * (i + 1), 0, 0);
      car.rotation.set(0, 0, 0);
      car.userData.lap = 1;
      car.userData.checkpoint = 0;
      car.userData.position = i + 2;
      car.userData.speed = 0;
      car.userData.angle = 0;
      car.userData.targetCheckpoint = 1;
      car.userData.recoveryTimer = 0;
    });
  }

  handleKeyDown(e) {
    this.keys[e.key.toLowerCase()] = true;
    if (e.key === 'c' || e.key === 'C') {
      this.cameraMode = (this.cameraMode + 1) % 3;
      this.updateHUD();
    }
    if (e.key === 'p' || e.key === 'Escape') {
      this.togglePause();
    }
    if (e.key === 'r' || e.key === 'R') {
      this.resetRace();
    }
  }

  handleKeyUp(e) {
    this.keys[e.key.toLowerCase()] = false;
  }

  handleResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  update() {
    if (this.gameState === 'racing') {
      this.updatePlayer();
      this.updateOpponents();
      this.updateCamera();
      this.updateHUD();
      this.checkRaceStatus();
    }
    this.renderer.render(this.scene, this.camera);
  }

  updatePlayer() {
    const car = this.playerCar;
    const data = car.userData;
    const speed = data.speed;

    // Acceleration
    if (this.keys['w'] || this.keys['arrowup']) {
      data.speed += data.acceleration;
    }
    // Braking
    if (this.keys['s'] || this.keys['arrowdown']) {
      data.speed -= data.braking;
    }
    // Reverse
    if (this.keys['s'] && data.speed < 0) {
      data.speed -= data.acceleration;
    }

    // Speed limits
    data.speed = Math.max(-data.maxSpeed / 2, Math.min(data.maxSpeed, data.speed));

    // Steering (speed-dependent)
    const turnFactor = Math.min(1, Math.abs(speed) / (data.maxSpeed * 0.3));
    if (this.keys['a'] || this.keys['arrowleft']) {
      data.angle += data.handling * turnFactor * (speed > 0 ? 1 : -1);
    }
    if (this.keys['d'] || this.keys['arrowright']) {
      data.angle -= data.handling * turnFactor * (speed > 0 ? 1 : -1);
    }

    // Apply movement
    car.position.x += Math.sin(data.angle) * speed;
    car.position.z += Math.cos(data.angle) * speed;
    car.rotation.y = data.angle;

    // Friction
    if (!this.keys['w'] && !this.keys['arrowup'] && !this.keys['s'] && !this.keys['arrowdown']) {
      data.speed *= 0.98;
    }

    // Checkpoint validation
    this.checkPlayerCheckpoint();

    // Lap counting
    this.checkPlayerLap();
  }

  updateOpponents() {
    this.opponentCars.forEach(car => {
      const data = car.userData;
      const speed = data.speed;

      // Simple AI: move towards next checkpoint
      const target = this.track.getCheckpointPosition(data.targetCheckpoint);
      const dx = target.x - car.position.x;
      const dz = target.z - car.position.z;
      const dist = Math.sqrt(dx * dx + dz * dz);

      // Calculate desired angle
      const desiredAngle = Math.atan2(dx, dz);
      let angleDiff = desiredAngle - data.angle;

      // Normalize angle
      while (angleDiff > Math.PI) angleDiff -= Math.PI * 2;
      while (angleDiff < -Math.PI) angleDiff += Math.PI * 2;

      // Steering
      if (Math.abs(angleDiff) > 0.1) {
        data.angle += Math.sign(angleDiff) * data.handling * 0.5;
      }

      // Speed control
      if (dist < 20) {
        data.speed *= 0.95; // Slow down for corners
      } else {
        data.speed += data.acceleration * 0.5;
      }

      // Apply movement
      car.position.x += Math.sin(data.angle) * speed;
      car.position.z += Math.cos(data.angle) * speed;
      car.rotation.y = data.angle;

      // Friction
      data.speed *= 0.99;

      // Checkpoint validation
      this.checkOpponentCheckpoint(car);

      // Lap counting
      this.checkOpponentLap(car);
    });

    // Update positions
    this.updatePositions();
  }

  updateCamera() {
    const car = this.playerCar;
    const data = car.userData;

    switch (this.cameraMode) {
      case 0: // Chase camera
        const chaseOffset = new THREE.Vector3(0, 5, -12);
        chaseOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), data.angle);
        this.camera.position.copy(car.position).add(chaseOffset);
        this.camera.lookAt(car.position.x, car.position.y + 2, car.position.z);
        break;

      case 1: // Hood camera
        this.camera.position.copy(car.position);
        this.camera.position.y += 1.5;
        this.camera.position.z -= 1;
        this.camera.lookAt(car.position.x, car.position.y + 1, car.position.z + 10);
        break;

      case 2: // Overhead camera
        this.camera.position.set(car.position.x, 30, car.position.z);
        this.camera.lookAt(car.position);
        break;
    }
  }

  updateHUD() {
    const car = this.playerCar;
    const data = car.userData;
    const speedKmh = Math.abs(data.speed * 100).toFixed(0);

    document.getElementById('speed').textContent = speedKmh;
    document.getElementById('lap').textContent = data.lap;
    document.getElementById('position').textContent = data.position;
    document.getElementById('timer').textContent = this.formatTime(this.totalRaceTime);
    document.getElementById('camera').textContent = ['Chase', 'Hood', 'Overhead'][this.cameraMode];
  }

  formatTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    const centiseconds = Math.floor((ms % 1000) / 10);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}.${centiseconds.toString().padStart(2, '0')}`;
  }

  checkPlayerCheckpoint() {
    const car = this.playerCar;
    const data = car.userData;
    const currentCheckpoint = data.checkpoint;
    const nextCheckpoint = (currentCheckpoint + 1) % this.track.checkpoints.length;
    const nextPos = this.track.getCheckpointPosition(nextCheckpoint);

    const dx = nextPos.x - car.position.x;
    const dz = nextPos.z - car.position.z;
    const dist = Math.sqrt(dx * dx + dz * dz);

    if (dist < 15) {
      data.checkpoint = nextCheckpoint;
    }
  }

  checkPlayerLap() {
    const car = this.playerCar;
    const data = car.userData;
    const startCheckpoint = 0;
    const nextCheckpoint = (data.checkpoint + 1) % this.track.checkpoints.length;
    const nextPos = this.track.getCheckpointPosition(nextCheckpoint);

    const dx = nextPos.x - car.position.x;
    const dz = nextPos.z - car.position.z;
    const dist = Math.sqrt(dx * dx + dz * dz);

    if (dist < 15 && data.checkpoint === startCheckpoint) {
      data.lap++;
      this.lapTimes.push(Date.now() - this.raceStartTime);
    }
  }

  checkOpponentCheckpoint(car) {
    const data = car.userData;
    const currentCheckpoint = data.checkpoint;
    const nextCheckpoint = (currentCheckpoint + 1) % this.track.checkpoints.length;
    const nextPos = this.track.getCheckpointPosition(nextCheckpoint);

    const dx = nextPos.x - car.position.x;
    const dz = nextPos.z - car.position.z;
    const dist = Math.sqrt(dx * dx + dz * dz);

    if (dist < 15) {
      data.checkpoint = nextCheckpoint;
    }
  }

  checkOpponentLap(car) {
    const data = car.userData;
    const startCheckpoint = 0;
    const nextCheckpoint = (data.checkpoint + 1) % this.track.checkpoints.length;
    const nextPos = this.track.getCheckpointPosition(nextCheckpoint);

    const dx = nextPos.x - car.position.x;
    const dz = nextPos.z - car.position.z;
    const dist = Math.sqrt(dx * dx + dz * dz);

    if (dist < 15 && data.checkpoint === startCheckpoint) {
      data.lap++;
    }
  }

  updatePositions() {
    const allCars = [this.playerCar, ...this.opponentCars];
    allCars.sort((a, b) => {
      if (b.userData.lap !== a.userData.lap) return b.userData.lap - a.userData.lap;
      if (a.userData.checkpoint !== b.userData.checkpoint) return b.userData.checkpoint - a.userData.checkpoint;
      const distA = this.getDistanceToNextCheckpoint(a);
      const distB = this.getDistanceToNextCheckpoint(b);
      return distA - distB;
    });

    allCars.forEach((car, index) => {
      car.userData.position = index + 1;
    });

    this.playerCar.userData.position = allCars.indexOf(this.playerCar) + 1;
  }

  getDistanceToNextCheckpoint(car) {
    const data = car.userData;
    const nextCheckpoint = (data.checkpoint + 1) % this.track.checkpoints.length;
    const nextPos = this.track.getCheckpointPosition(nextCheckpoint);
    const dx = nextPos.x - car.position.x;
    const dz = nextPos.z - car.position.z;
    return Math.sqrt(dx * dx + dz * dz);
  }

  checkRaceStatus() {
    if (this.playerCar.userData.lap > NUM_LAPS) {
      this.gameState = 'results';
      this.showResults();
    }
  }

  showResults() {
    this.resultsDiv.style.display = 'flex';
    const resultsList = document.getElementById('resultsList');
    const allCars = [this.playerCar, ...this.opponentCars];
    allCars.sort((a, b) => b.userData.lap - a.userData.lap);

    resultsList.innerHTML = '';
    allCars.forEach((entry, index) => {
      const div = document.createElement('div');
      div.textContent = `${index + 1}. ${entry.userData.isPlayer ? 'You' : 'Opponent'} - Lap ${entry.userData.lap}`;
      resultsList.appendChild(div);
    });
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.update();
  }
}

// Initialize Game
new Game();
