import * as THREE from 'three';

export class Car {
    constructor(stats, isPlayer, waypoints, npcIndex = 0) {
        this.maxSpeed = stats.maxSpeed;
        this.acceleration = stats.acceleration;
        this.braking = stats.braking;
        this.handling = stats.handling;
        this.color = stats.color;
        this.isPlayer = isPlayer;
        this.waypoints = waypoints;
        this.npcIndex = npcIndex;
        this.speed = 0;
        this.angle = 0;
        this.lap = 1;
        this.lastCheckpoint = -1;
        this.racePosition = 1;
        this.collisions = 0;
        this.stuckTimer = 0;
        this.recoveries = 0;
        this.mesh = this.createMesh();
        this.reset();
    }

    createMesh() {
        const group = new THREE.Group();
        const bodyGeo = new THREE.BoxGeometry(2, 0.8, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: this.color });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.6;
        body.castShadow = true;
        group.add(body);
        const cabinGeo = new THREE.BoxGeometry(1.5, 0.6, 2);
        const cabinMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const cabin = new THREE.Mesh(cabinGeo, cabinMat);
        cabin.position.y = 1.3;
        cabin.position.z = -0.2;
        cabin.castShadow = true;
        group.add(cabin);
        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const positions = [[-1.2, 0.4, 1.2], [1.2, 0.4, 1.2], [-1.2, 0.4, -1.2], [1.2, 0.4, -1.2]];
        positions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(...pos);
            wheel.castShadow = true;
            group.add(wheel);
        });
        const spoilerGeo = new THREE.BoxGeometry(2.2, 0.1, 0.6);
        const spoilerMat = new THREE.MeshStandardMaterial({ color: this.color });
        const spoiler = new THREE.Mesh(spoilerGeo, spoilerMat);
        spoiler.position.set(0, 1.4, -1.8);
        group.add(spoiler);
        return group;
    }

    reset() {
        this.speed = 0;
        this.angle = 0;
        this.lap = 1;
        this.lastCheckpoint = -1;
        this.racePosition = 1;
        this.collisions = 0;
        this.stuckTimer = 0;
        this.recoveries = 0;
        const startWP = this.waypoints[0];
        this.mesh.position.set(startWP.x, 0.5, startWP.z);
        this.mesh.rotation.set(0, 0, 0);
    }

    update(deltaTime, accelerate, brake, steerLeft, steerRight, otherCars) {
        if (this.isPlayer) {
            this.handlePlayerInput(deltaTime, accelerate, brake, steerLeft, steerRight);
        } else {
            this.handleAI(deltaTime, otherCars);
        }
        this.applyPhysics(deltaTime);
        this.checkStuck();
    }

    handlePlayerInput(dt, acc, brk, left, right) {
        if (acc) this.speed += this.acceleration * 10 * dt;
        else if (brk) this.speed -= this.braking * 20 * dt;
        else this.speed *= 0.98;
        const turnSpeed = this.handling * 3 * (this.speed / this.maxSpeed);
        if (left) this.angle += turnSpeed * dt;
        if (right) this.angle -= turnSpeed * dt;
        this.speed = Math.max(-this.maxSpeed * 0.3, Math.min(this.maxSpeed, this.speed));
    }

    handleAI(dt, otherCars) {
        const targetWP = this.waypoints[this.lastCheckpoint + 1];
        if (!targetWP) return;
        const dx = targetWP.x - this.mesh.position.x;
        const dz = targetWP.z - this.mesh.position.z;
        const distToTarget = Math.sqrt(dx * dx + dz * dz);
        const desiredAngle = Math.atan2(dx, dz);
        let angleDiff = desiredAngle - this.angle;
        while (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
        while (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;
        const turnSpeed = this.handling * 4;
        if (Math.abs(angleDiff) > 0.1) {
            this.angle += Math.sign(angleDiff) * turnSpeed * dt;
        }
        let targetSpeed = this.maxSpeed * 0.9;
        for (const other of otherCars) {
            if (other === this) continue;
            const odx = other.mesh.position.x - this.mesh.position.x;
            const odz = other.mesh.position.z - this.mesh.position.z;
            const oDist = Math.sqrt(odx * odx + odz * odz);
            if (oDist < 10 && oDist > 2) {
                targetSpeed = Math.min(targetSpeed, this.maxSpeed * 0.6);
            }
        }
        if (this.speed < targetSpeed) this.speed += this.acceleration * 8 * dt;
        else this.speed *= 0.99;
        this.speed = Math.max(0, Math.min(this.maxSpeed, this.speed));
    }

    applyPhysics(dt) {
        const velocityX = Math.sin(this.angle) * this.speed;
        const velocityZ = Math.cos(this.angle) * this.speed;
        this.mesh.position.x += velocityX * dt;
        this.mesh.position.z += velocityZ * dt;
        this.mesh.rotation.y = this.angle;
    }

    checkStuck() {
        if (Math.abs(this.speed) < 1 && this.stuckTimer > 2) {
            this.recoveries++;
            const targetWP = this.waypoints[this.lastCheckpoint + 1];
            if (targetWP) {
                this.mesh.position.x += Math.sin(this.angle) * 2;
                this.mesh.position.z += Math.cos(this.angle) * 2;
                this.speed = 30;
            }
        }
        if (Math.abs(this.speed) < 1) this.stuckTimer++;
        else this.stuckTimer = 0;
    }
}
