    .lap - b.car.userData.lap) || (a.car.userData.lap - b.car.userData.lap) || (a.car.userData.position - b.car.userData.position);
      allCars.forEach((entry, index) => {
        const div = document.createElement('div');
        div.textContent = `${index + 1}. ${entry.name} - Lap ${entry.car.userData.lap}`;
        resultsList.appendChild(div);
      });
    }

    showMenu() {
      this.gameState = 'menu';
      this.menuDiv.style.display = 'flex';
      this.hudDiv.style.display = 'none';
      this.pauseDiv.style.display = 'none';
      this.resultsDiv.style.display = 'none';
    }

    init() {
      this.setupScene();
      this.createTrack();
      this.createCars();
      this.createUI();
      this.animate();
    }

    animate() {
      requestAnimationFrame(() => this.animate());
      this.update();
    }

    // Input handling
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
      if (e.key === 'c' || e.key === 'C') {
        this.cameraMode = (this.cameraMode + 1) % 3;
      }
      if (e.key === 'p' || e.key === 'Escape') {
        this.togglePause();
      }
      if (e.key === 'r' || e.key === 'R') {
        this.resetRace();
      }
    });

    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
    });

    // Start the game
    new Game();
  }
}

// Initialize Game
const CARS = [
  { name: 'Speedster', color: 0xff0000, maxSpeed: 1.2, acceleration: 0.02, braking: 0.05, handling: 0.04 },
  { name: 'Tank', color: 0x00ff00, maxSpeed: 0.9, acceleration: 0.03, braking: 0.08, handling: 0.02 },
  { name: 'Drift King', color: 0x0000ff, maxSpeed: 1.1, acceleration: 0.025, braking: 0.04, handling: 0.06 }
];

const TRACK_POINTS = [
  { x: 0, z: 0 },
  { x: 50, z: 0 },
  { x: 100, z: 20 },
  { x: 150, z: 0 },
  { x: 200, z: -30 },
  { x: 150, z: -80 },
  { x: 100, z: -100 },
  { x: 50, z: -80 },
  { x: 0, z: -50 },
  { x: -50, z: -80 },
  { x: -100, z: -50 },
  { x: -150, z: 0 },
  { x: -100, z: 50 },
  { x: -50, z: 100 },
  { x: 0, z: 100 },
  { x: 50, z: 50 }
];

const TRACK_WIDTH = 20;

new Game();