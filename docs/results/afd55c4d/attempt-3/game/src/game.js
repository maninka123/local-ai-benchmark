import * as THREE from 'three';
import { Car } from './car.js';
import { Track } from './track.js';
import { UI } from './ui.js';

export class Game {
    constructor() {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(this.renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(50, 100, 50);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        dirLight.shadow.camera.near = 0.5;
        dirLight.shadow.camera.far = 500;
        dirLight.shadow.camera.left = -100;
        dirLight.shadow.camera.right = 100;
        dirLight.shadow.camera.top = 100;
        dirLight.shadow.camera.bottom = -100;
        this.scene.add(dirLight);

        // Sky color
        this.scene.background = new THREE.Color(0x87ceeb);

        // Game state
        this.state = 'MENU'; // MENU, COUNTDOWN, RACING, PAUSED, FINISHED
        this.selectedCarIndex = 0;
        this.playerCar = null;
        this.npcCars = [];
        this.track = null;
        this.ui = new UI();
        
        // Race state
        this.countdownValue = 3;
        this.countdownTimer = 0;
        this.raceStartTime = 0;
        this.lapsCompleted = 0;
        this.totalLaps = 3;
        this.currentCheckpoint = -1;
        this.checkpointsPassed = [];
        
        // Camera
        this.cameraMode = 0; // 0: chase, 1: hood, 2: overhead
        
        // Input
        this.keys = {};
        this.setupInput();
        
        // Resize handler
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Initialize menu
        this.initMenu();
    }

    setupInput() {
        document.addEventListener('keydown', (e) => {
            this.keys[e.key.toLowerCase()] = true;
            
            if (this.state === 'RACING') {
                if (e.key.toLowerCase() === 'c') this.switchCamera();
                if (e.key === 'Escape' || e.key.toLowerCase() === 'p') this.togglePause();
                if (e.key.toLowerCase() === 'r') this.restartRace();
            }
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.key.toLowerCase()] = false;
        });
    }

    initMenu() {
        this.ui.showMenu();
        this.ui.updateCarSelection(0);
        
        // Car selection buttons
        const carButtons = document.querySelectorAll('.car-select-btn');
        carButtons.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                this.selectedCarIndex = index;
                this.ui.updateCarSelection(index);
            });
        });
        
        // Start button
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this.startRace();
            });
        }
    }

    startRace() {
        // Clear previous race
        if (this.playerCar) {
            this.scene.remove(this.playerCar.mesh);
        }
        this.npcCars.forEach(npc => this.scene.remove(npc.mesh));
        if (this.track) {
            // Remove track elements would require tracking them
        }
        
        // Create new track
        this.track = new Track(this.scene);
        
        // Create player car with selected stats
        const carStats = this.ui.getCarStats(this.selectedCarIndex);
        this.playerCar = new Car(this.scene, 0, -60, carStats, true);
        
        // Create NPC cars at different starting positions
        const npcColors = [0xff4444, 0x44ff44, 0x4444ff, 0xffff44];
        const npcStartPositions = [
            { x: -5, z: -60 },
            { x: 5, z: -60 },
            { x: -10, z: -65 },
            { x: 10, z: -65 }
        ];
        
        const npcStats = [
            { maxSpeed: 42, acceleration: 0.38, braking: 0.45, handling: 0.78 },
            { maxSpeed: 45, acceleration: 0.35, braking: 0.42, handling: 0.75 },
            { maxSpeed: 40, acceleration: 0.42, braking: 0.48, handling: 0.82 },
            { maxSpeed: 43, acceleration: 0.36, braking: 0.44, handling: 0.76 }
        ];
        
        this.npcCars = npcStartPositions.map((pos, i) => {
            const npc = new Car(this.scene, pos.x, pos.z, npcStats[i], false, npcColors[i]);
            return npc;
        });
        
        // Reset race state
        this.state = 'COUNTDOWN';
        this.countdownValue = 3;
        this.countdownTimer = 0;
        this.lapsCompleted = 0;
        this.currentCheckpoint = -1;
        this.checkpointsPassed = [];
        
        // Reset all cars
        this.playerCar.reset(0, -60);
        this.npcCars.forEach((npc, i) => {
            npc.reset(npcStartPositions[i].x, npcStartPositions[i].z);
        });
        
        // Hide menu, show HUD
        this.ui.hideMenu();
        this.ui.showHUD();
    }

    switchCamera() {
        this.cameraMode = (this.cameraMode + 1) % 3;
        this.ui.updateCameraIndicator(this.cameraMode);
    }

    togglePause() {
        if (this.state === 'RACING') {
            this.state = 'PAUSED';
            this.ui.showPause();
        } else if (this.state === 'PAUSED') {
            this.state = 'RACING';
            this.raceStartTime += performance.now() - this.raceStartTime;
            this.ui.hidePause();
        }
    }

    restartRace() {
        this.startRace();
    }

    update(dt) {
        if (this.state === 'COUNTDOWN') {
            this.updateCountdown(dt);
        } else if (this.state === 'RACING') {
            this.updateRace(dt);
        }
        
        // Update all cars
        if (this.playerCar && this.state !== 'PAUSED') {
            this.playerCar.update(dt, this.keys);
        }
        
        this.npcCars.forEach(npc => {
            if (this.state !== 'PAUSED') {
                npc.updateAI(dt, this.track.waypoints, this.playerCar, this.npcCars);
            }
        });
        
        // Update camera
        this.updateCamera();
        
        // Check collisions
        this.checkCollisions();
        
        // Update UI
        if (this.state === 'RACING' || this.state === 'PAUSED') {
            this.ui.updateHUD(this.playerCar, this.lapsCompleted, this.totalLaps, this.getRacePosition());
        }
    }

    updateCountdown(dt) {
        this.countdownTimer += dt;
        if (this.countdownTimer >= 1) {
            this.countdownTimer = 0;
            this.countdownValue--;
            
            if (this.countdownValue <= 0) {
                this.state = 'RACING';
                this.raceStartTime = performance.now();
                this.ui.hideCountdown();
            } else {
                this.ui.showCountdown(this.countdownValue);
            }
        }
    }

    updateRace(dt) {
        // Update checkpoints for player
        this.updateCheckpoints(this.playerCar);
        
        // Check race completion
        if (this.lapsCompleted >= this.totalLaps) {
            this.finishRace();
        }
        
        // Update NPC checkpoints and laps
        this.npcCars.forEach(npc => {
            npc.updateCheckpoints(this.track.checkpoints);
        });
    }

    updateCheckpoints(car) {
        const carPos = car.mesh.position;
        
        // Check if we've passed the next checkpoint
        for (let i = 0; i < this.track.checkpoints.length; i++) {
            const cp = this.track.checkpoints[i];
            const dist = Math.sqrt(
                (carPos.x - cp.x) ** 2 + 
                (carPos.z - cp.z) ** 2
            );
            
            if (dist < cp.radius && i === this.currentCheckpoint + 1) {
                this.currentCheckpoint = i;
                this.checkpointsPassed.push(i);
                
                // Check if lap is complete
                if (i === this.track.checkpoints.length - 1) {
                    this.lapsCompleted++;
                    this.currentCheckpoint = -1;
                    this.checkpointsPassed = [];
                }
            }
        }
    }

    getRacePosition() {
        // Calculate position based on progress through checkpoints and laps
        const playerProgress = this.lapsCompleted * 100 + 
                              (this.currentCheckpoint + 1) / this.track.checkpoints.length * 100;
        
        let positions = [playerProgress];
        this.npcCars.forEach(npc => {
            const npcProgress = npc.lapsCompleted * 100 + 
                               (npc.currentCheckpoint + 1) / this.track.checkpoints.length * 100;
            positions.push(npcProgress);
        });
        
        positions.sort((a, b) => b - a);
        return positions.indexOf(playerProgress) + 1;
    }

    updateCamera() {
        if (!this.playerCar) return;
        
        const carPos = this.playerCar.mesh.position;
        const carDir = new THREE.Vector3();
        this.playerCar.mesh.getWorldDirection(carDir);
        
        switch (this.cameraMode) {
            case 0: // Chase camera
                const chaseOffset = new THREE.Vector3(0, 5, -12);
                chaseOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), this.playerCar.mesh.rotation.y);
                this.camera.position.copy(carPos).add(chaseOffset);
                this.camera.lookAt(carPos.x, carPos.y + 2, carPos.z);
                break;
                
            case 1: // Hood/cockpit camera
                const hoodOffset = new THREE.Vector3(0, 1.5, -0.5);
                hoodOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), this.playerCar.mesh.rotation.y);
                this.camera.position.copy(carPos).add(hoodOffset);
                const lookAhead = new THREE.Vector3(0, 1.5, -15);
                lookAhead.applyAxisAngle(new THREE.Vector3(0, 1, 0), this.playerCar.mesh.rotation.y);
                this.camera.lookAt(carPos.add(lookAhead));
                break;
                
            case 2: // Overhead camera
                this.camera.position.set(carPos.x, 40, carPos.z);
                this.camera.lookAt(carPos.x, 0, carPos.z);
                break;
        }
    }

    checkCollisions() {
        const cars = [this.playerCar, ...this.npcCars];
        
        // Car-to-car collisions
        for (let i = 0; i < cars.length; i++) {
            for (let j = i + 1; j < cars.length; j++) {
                const car1 = cars[i];
                const car2 = cars[j];
                
                const dist = car1.mesh.position.distanceTo(car2.mesh.position);
                if (dist < 3) {
                    // Simple collision response - push apart
                    const dir = new THREE.Vector3().subVectors(car1.mesh.position, car2.mesh.position).normalize();
                    const overlap = 3 - dist;
                    
                    car1.mesh.position.add(dir.multiplyScalar(overlap / 2));
                    car2.mesh.position.sub(dir.multiplyScalar(overlap / 2));
                    
                    // Reduce speeds
                    car1.speed *= 0.7;
                    car2.speed *= 0.7;
                }
            }
        }
        
        // Car-to-barrier collisions
        cars.forEach(car => {
            this.track.barriers.forEach(barrier => {
                const dist = car.mesh.position.distanceTo(barrier.position);
                if (dist < 2) {
                    // Push car away from barrier
                    const dir = new THREE.Vector3().subVectors(car.mesh.position, barrier.position).normalize();
                    car.mesh.position.add(dir.multiplyScalar(0.5));
                    car.speed *= 0.5;
                }
            });
        });
    }

    finishRace() {
        this.state = 'FINISHED';
        
        // Calculate final standings
        const standings = [];
        standings.push({ name: 'Player', carIndex: this.selectedCarIndex, laps: this.lapsCompleted, checkpoint: this.currentCheckpoint });
        
        this.npcCars.forEach((npc, i) => {
            standings.push({ name: `NPC ${i + 1}`, carIndex: -1, laps: npc.lapsCompleted, checkpoint: npc.currentCheckpoint });
        });
        
        // Sort by progress
        standings.sort((a, b) => {
            if (a.laps !== b.laps) return b.laps - a.laps;
            return b.checkpoint - a.checkpoint;
        });
        
        this.ui.showResults(standings);
    }

    render() {
        this.renderer.render(this.scene, this.camera);
    }
}
