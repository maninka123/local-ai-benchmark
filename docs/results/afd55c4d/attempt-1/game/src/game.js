import * as THREE from 'three';
import { Car } from './car.js';
import { Track } from './track.js';
import { UI } from './ui.js';

export class Game {
    constructor(container) {
        this.container = container;
        this.NUM_LAPS = 3;
        this.NUM_NPCS = 4;
        this.CAR_STATS = {
            red: { name: "Red Racer", maxSpeed: 180, acceleration: 0.8, braking: 0.9, handling: 0.75, color: 0xff3333 },
            blue: { name: "Blue Bolt", maxSpeed: 160, acceleration: 1.0, braking: 0.85, handling: 0.85, color: 0x3333ff },
            green: { name: "Green Machine", maxSpeed: 200, acceleration: 0.6, braking: 0.95, handling: 0.70, color: 0x33ff33 }
        };
        this.STATE = { MENU: 0, CAR_SELECT: 1, COUNTDOWN: 2, RACING: 3, PAUSED: 4, FINISHED: 5 };
        this.CAMERA = { CHASE: 0, HOOD: 1, OVERHEAD: 2 };
        this.scene = null; this.camera = null; this.renderer = null;
        this.playerCar = null; this.npcCars = []; this.track = null;
        this.checkpoints = []; this.waypoints = [];
        this.gameState = this.STATE.MENU;
        this.selectedCarIndex = 0;
        this.currentCamera = this.CAMERA.CHASE;
        this.countdownValue = 3;
        this.raceStartTime = 0;
        this.playerLap = 1;
        this.playerBestLap = Infinity;
        this.lastCheckpoint = -1;
        this.finishTimes = [];
        this.keys = { up: false, down: false, left: false, right: false };
        this.ui = null;
        this.animationId = null;
        this.lastTime = 0;
    }

    init() {
        this.setupScene();
        this.setupLighting();
        this.track = new Track(this.scene);
        this.waypoints = this.track.waypoints;
        this.checkpoints = this.track.checkpoints;
        const stats = Object.values(this.CAR_STATS)[this.selectedCarIndex];
        this.playerCar = new Car(stats, true, this.waypoints);
        this.scene.add(this.playerCar.mesh);
        for (let i = 0; i < this.NUM_NPCS; i++) {
            const npcStats = Object.values(this.CAR_STATS)[i % 3];
            const npc = new Car(npcStats, false, this.waypoints, i);
            this.npcCars.push(npc);
            this.scene.add(npc.mesh);
        }
        this.ui = new UI(this.container, this);
        window.addEventListener('resize', () => this.onWindowResize());
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
        document.addEventListener('keyup', (e) => this.onKeyUp(e));
        window.__BENCHMARK__ = { snapshot: () => this.getSnapshot(), step: (s, dt) => this.stepSimulation(s, dt) };
        this.lastTime = performance.now();
        this.animate();
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87CEEB);
        this.scene.fog = new THREE.Fog(0x87CEEB, 100, 500);
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
    }

    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 200, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);
    }

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    onKeyDown(event) {
        switch (event.code) {
            case 'KeyW': case 'ArrowUp': this.keys.up = true; break;
            case 'KeyS': case 'ArrowDown': this.keys.down = true; break;
            case 'KeyA': case 'ArrowLeft': this.keys.left = true; break;
            case 'KeyD': case 'ArrowRight': this.keys.right = true; break;
            case 'KeyC': this.switchCamera(); break;
            case 'KeyP': case 'Escape': this.togglePause(); break;
            case 'KeyR': if (this.gameState === this.STATE.FINISHED) this.restartRace(); break;
        }
    }

    onKeyUp(event) {
        switch (event.code) {
            case 'KeyW': case 'ArrowUp': this.keys.up = false; break;
            case 'KeyS': case 'ArrowDown': this.keys.down = false; break;
            case 'KeyA': case 'ArrowLeft': this.keys.left = false; break;
            case 'KeyD': case 'ArrowRight': this.keys.right = false; break;
        }
    }

    switchCamera() {
        this.currentCamera = (this.currentCamera + 1) % 3;
        this.ui.updateCameraIndicator(this.currentCamera);
    }

    togglePause() {
        if (this.gameState === this.STATE.RACING) {
            this.gameState = this.STATE.PAUSED;
            this.ui.showPause();
        } else if (this.gameState === this.STATE.PAUSED) {
            this.gameState = this.STATE.RACING;
            this.raceStartTime += (performance.now() - this.lastTime) / 1000;
            this.ui.hidePause();
        }
    }

    restartRace() {
        this.gameState = this.STATE.MENU;
        this.playerLap = 1;
        this.playerBestLap = Infinity;
        this.lastCheckpoint = -1;
        this.finishTimes = [];
        if (this.playerCar) this.playerCar.reset();
        this.npcCars.forEach(npc => npc.reset());
        this.ui.showMenu();
    }

    startRace() {
        this.gameState = this.STATE.COUNTDOWN;
        this.countdownValue = 3;
        this.raceStartTime = performance.now();
        this.playerLap = 1;
        this.playerBestLap = Infinity;
        this.lastCheckpoint = -1;
        this.finishTimes = [];
        this.playerCar.reset();
        this.npcCars.forEach(npc => npc.reset());
        this.ui.hideMenu();
        this.ui.showCountdown(this.countdownValue);
    }

    selectCar(index) {
        this.selectedCarIndex = index;
        this.ui.updateCarSelection(index);
    }

    update(deltaTime) {
        if (this.gameState === this.STATE.COUNTDOWN) {
            this.handleCountdown(deltaTime);
        } else if (this.gameState === this.STATE.RACING) {
            this.handleRacing(deltaTime);
        }
        this.updateCamera();
    }

    handleCountdown(deltaTime) {
        this.countdownValue -= deltaTime;
        if (this.countdownValue <= 0) {
            if (this.countdownValue < -1) {
                this.gameState = this.STATE.RACING;
                this.ui.hideCountdown();
                this.ui.showHUD();
            } else {
                this.countdownValue = Math.floor(this.countdownValue) + 1;
                this.ui.updateCountdown(Math.max(1, Math.floor(this.countdownValue)));
            }
        } else {
            this.ui.updateCountdown(Math.ceil(this.countdownValue));
        }
    }

    handleRacing(deltaTime) {
        this.playerCar.update(deltaTime, this.keys.up, this.keys.down, this.keys.left, this.keys.right, this.npcCars);
        this.npcCars.forEach(npc => npc.update(deltaTime, false, false, false, false, [this.playerCar, ...this.npcCars]));
        this.checkCollisions();
        this.updateLapTracking();
        this.updateRacePositions();
        this.ui.updateHUD(this.playerCar.speed, this.playerLap, this.NUM_LAPS, this.getPlayerPosition(), this.getRaceTime());
    }

    checkCollisions() {
        const allCars = [this.playerCar, ...this.npcCars];
        for (let i = 0; i < allCars.length; i++) {
            for (let j = i + 1; j < allCars.length; j++) {
                const car1 = allCars[i], car2 = allCars[j];
                const dx = car1.mesh.position.x - car2.mesh.position.x;
                const dz = car1.mesh.position.z - car2.mesh.position.z;
                const distance = Math.sqrt(dx * dx + dz * dz);
                if (distance < 3) {
                    const bounceDirX = dx / distance, bounceDirZ = dz / distance;
                    car1.speed *= 0.8; car2.speed *= 0.8;
                    car1.mesh.position.x += bounceDirX * 1;
                    car1.mesh.position.z += bounceDirZ * 1;
                    car2.mesh.position.x -= bounceDirX * 1;
                    car2.mesh.position.z -= bounceDirZ * 1;
                }
            }
        }
    }

    updateLapTracking() {
        const pos = this.playerCar.mesh.position;
        for (let i = 0; i < this.checkpoints.length; i++) {
            const cp = this.checkpoints[i];
            const dist = Math.sqrt((pos.x - cp.x) ** 2 + (pos.z - cp.z) ** 2);
            if (dist < cp.radius && i > this.lastCheckpoint) this.lastCheckpoint = i;
        }
        if (this.lastCheckpoint >= this.checkpoints.length - 1) {
            const finishLineDist = Math.sqrt(pos.x * pos.x + pos.z * pos.z);
            if (finishLineDist < 20) this.completeLap();
        }
    }

    completeLap() {
        if (this.playerLap <= this.NUM_LAPS) {
            const lapTime = this.getRaceTime();
            if (lapTime < this.playerBestLap) this.playerBestLap = lapTime;
            this.playerLap++;
            this.lastCheckpoint = -1;
        }
    }

    updateRacePositions() {
        const allCars = [{ car: this.playerCar, isPlayer: true }, ...this.npcCars.map((npc, i) => ({ car: npc, isPlayer: false }))];
        allCars.sort((a, b) => {
            if (a.car.lap !== b.car.lap) return b.car.lap - a.car.lap;
            if (a.car.lastCheckpoint !== b.car.lastCheckpoint) return b.car.lastCheckpoint - a.car.lastCheckpoint;
            const distA = Math.sqrt(a.car.mesh.position.x ** 2 + a.car.mesh.position.z ** 2);
            const distB = Math.sqrt(b.car.mesh.position.x ** 2 + b.car.mesh.position.z ** 2);
            return distB - distA;
        });
        allCars.forEach((item, index) => item.car.racePosition = index + 1);
    }

    getPlayerPosition() { return this.playerCar.racePosition || 1; }
    getRaceTime() {
        if (this.gameState !== this.STATE.RACING && this.gameState !== this.STATE.PAUSED) return 0;
        return (performance.now() - this.raceStartTime) / 1000;
    }

    updateCamera() {
        if (!this.playerCar || !this.camera) return;
        const carPos = this.playerCar.mesh.position;
        const carRot = this.playerCar.mesh.rotation.y;
        switch (this.currentCamera) {
            case this.CAMERA.CHASE:
                const chaseOffset = new THREE.Vector3(0, 8, -15);
                chaseOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), carRot);
                this.camera.position.copy(carPos).add(chaseOffset);
                this.camera.lookAt(carPos.x, carPos.y + 2, carPos.z);
                break;
            case this.CAMERA.HOOD:
                const hoodOffset = new THREE.Vector3(0, 1.5, 1);
                hoodOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), carRot);
                this.camera.position.copy(carPos).add(hoodOffset);
                this.camera.lookAt(carPos.x + Math.sin(carRot) * 20, carPos.y + 2, carPos.z + Math.cos(carRot) * 20);
                break;
            case this.CAMERA.OVERHEAD:
                this.camera.position.set(carPos.x, 50, carPos.z);
                this.camera.lookAt(carPos.x, 0, carPos.z);
                break;
        }
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        const now = performance.now();
        const deltaTime = Math.min((now - this.lastTime) / 1000, 0.1);
        this.lastTime = now;
        if (this.gameState !== this.STATE.PAUSED) this.update(deltaTime);
        this.renderer.render(this.scene, this.camera);
    }

    getSnapshot() {
        return {
            selectedCar: Object.keys(this.CAR_STATS)[this.selectedCarIndex],
            playerPosition: [this.playerCar?.mesh.position.x || 0, this.playerCar?.mesh.position.y || 0, this.playerCar?.mesh.position.z || 0],
            elapsed: this.getRaceTime(),
            camera: this.currentCamera,
            npcs: this.npcCars.map(n => ({ laps: n.lap, collisions: n.collisions || 0, stuck: false, recoveries: 0 }))
        };
    }

    stepSimulation(seconds, dt) {
        for (let i = 0; i < seconds / dt; i++) this.update(dt);
    }
}
