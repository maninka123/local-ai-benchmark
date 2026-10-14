import * as THREE from 'three';
import { CHECKPOINTS } from './constants.js';

export class Vehicle {
    constructor(scene, config, isPlayer = false, isNPC = false) {
        this.config = config;
        this.isPlayer = isPlayer;
        this.isNPC = isNPC;
        this.scene = scene;
        
        this.velocity = new THREE.Vector3();
        this.speed = 0;
        this.steering = 0;
        this.rotation = 0;
        
        this.lap = 0;
        this.checkpointIndex = 0;
        this.isFinished = false;
        this.lastCheckpointTime = 0;

        // Visuals
        this.mesh = new THREE.Group();
        
        // Body
        const bodyGeom = new THREE.BoxGeometry(1.5, 0.6, 3);
        const bodyMat = new THREE.MeshStandardMaterial({ color: config.color });
        const body = new THREE.Mesh(bodyGeom, bodyMat);
        body.position.y = 0.5;
        this.mesh.add(body);

        // Cockpit
        const cockpitGeom = new THREE.BoxGeometry(1, 0.5, 1.2);
        const cockpitMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const cockpit = new THREE.Mesh(cockpitGeom, cockpitMat);
        cockpit.position.set(0, 0.9, -0.2);
        this.mesh.add(cockpit);

        // Wheels
        const wheelGeom = new THREE.CylinderGeometry(0.35, 0.35, 0.4, 12);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        const wheelPositions = [
            [-0.8, 0.35, 1], [0.8, 0.35, 1], 
            [-0.8, 0.35, -1], [0.8, 0.35, -1]
        ];
        
        wheelPositions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeom, wheelMat);
            wheel.position.set(pos[0], pos[1], pos[2]);
            wheel.rotation.z = Math.PI / 2;
            this.mesh.add(wheel);
        });

        this.scene.add(this.mesh);
    }

    update(dt, input, trackWaypoints) {
        if (this.isFinished) return;

        if (this.isPlayer) {
            this.handlePlayerInput(input, dt);
        } else if (this.isNPC) {
            this.handleNPCLogic(trackWaypoints, dt);
        }

        // Apply physics
        const direction = new THREE.Vector3(0, 0, 1).applyQuaternion(this.mesh.quaternion);
        this.velocity.copy(direction.multiplyScalar(this.speed));
        this.mesh.position.add(this.velocity.clone().multiplyScalar(dt));

        // Friction/Drag
        this.speed *= (1 - 0.95 * dt);
        if (Math.abs(this.speed) < 0.01) this.speed = 0;

        // Checkpoints
        this.checkCheckpoints();
    }

    handlePlayerInput(input, dt) {
        if (input.forward) this.speed += this.config.acceleration;
        if (input.backward) this.speed -= this.config.braking;
        
        if (input.left) this.steering += this.config.handling * dt;
        if (input.right) this.steering -= this.config.handling * dt;

        this.steering *= 0.9; // Steering centering
        this.mesh.rotation.y += this.steering * (this.speed * 0.5);
        
        if (this.speed > this.config.maxSpeed) this.speed = this.config.maxSpeed;
        if (this.speed < -this.config.maxSpeed/2) this.speed = -this.config.maxSpeed/2;
    }

    handleNPCLogic(waypoints, dt) {
        const target = waypoints[this.checkpointIndex];
        const dist = this.mesh.position.distanceTo(target);

        if (dist < 10) {
            this.checkpointIndex = (this.checkpointIndex + 1) % waypoints.length;
        }

        const targetDir = new THREE.Vector3().subVectors(target, this.mesh.position).normalize();
        const currentDir = new THREE.Vector3(0, 0, 1).applyQuaternion(this.mesh.quaternion);
        
        // Simple steering towards target
        const dot = currentDir.dot(targetDir);
        if (dot < 0.95) {
            const angle = Math.acos(Math.max(-1, Math.min(1, dot)));
            const axis = new THREE.Vector3().crossVectors(currentDir, targetDir).normalize();
            this.mesh.rotateOnWorldAxis(axis, angle * 0.1);
        }

        // Speed control
        const speedTarget = targetDir.dot(currentDir) > 0 ? this.config.maxSpeed * 0.8 : -this.config.maxSpeed * 0.2;
        if (this.speed < speedTarget) this.speed += this.config.acceleration;
        if (this.speed > speedTarget) this.speed -= this.config.braking;
    }

    checkCheckpoints() {
        const cp = CHECKPOINTS[this.checkpointIndex];
        if (this.mesh.position.distanceTo(cp) < 15) {
            this.checkpointIndex = (this.checkpointIndex + 1) % CHECKPOINTS.length;
            if (this.checkpointIndex === 0) {
                this.lap++;
                // Check if race finished (e.g., 3 laps)
                if (this.lap >= 3) this.isFinished = true;
            }
        }
    }
}
