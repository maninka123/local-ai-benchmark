import * as THREE from 'three';

export class Car {
    constructor(scene, x, z, stats, isPlayer = false, color = 0xff6600) {
        this.scene = scene;
        this.stats = stats || { maxSpeed: 40, acceleration: 0.4, braking: 0.5, handling: 0.8 };
        this.isPlayer = isPlayer;
        
        // Physics state
        this.speed = 0;
        this.maxSpeed = this.stats.maxSpeed;
        this.acceleration = this.stats.acceleration;
        this.braking = this.stats.braking;
        this.handling = this.stats.handling;
        this.friction = 0.96;
        
        // Position and rotation
        this.mesh = this.createCarMesh(color);
        this.mesh.position.set(x, 0.5, z);
        this.scene.add(this.mesh);
        
        // AI state
        this.currentWaypoint = 0;
        this.currentCheckpoint = -1;
        this.lapsCompleted = 0;
        this.checkpointsPassed = [];
        this.stuckTimer = 0;
        this.recoveryMode = false;
    }

    createCarMesh(color) {
        const carGroup = new THREE.Group();
        
        // Car body
        const bodyGeo = new THREE.BoxGeometry(2, 0.8, 4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: color });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.6;
        body.castShadow = true;
        carGroup.add(body);
        
        // Car cabin
        const cabinGeo = new THREE.BoxGeometry(1.6, 0.6, 2);
        const cabinMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const cabin = new THREE.Mesh(cabinGeo, cabinMat);
        cabin.position.y = 1.2;
        cabin.position.z = -0.2;
        cabin.castShadow = true;
        carGroup.add(cabin);
        
        // Wheels
        const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        
        const wheelPositions = [
            { x: -1.1, z: 1.2 },
            { x: 1.1, z: 1.2 },
            { x: -1.1, z: -1.2 },
            { x: 1.1, z: -1.2 }
        ];
        
        wheelPositions.forEach(pos => {
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(pos.x, 0.4, pos.z);
            wheel.castShadow = true;
            carGroup.add(wheel);
        });
        
        // Headlights
        const lightGeo = new THREE.BoxGeometry(0.3, 0.2, 0.1);
        const lightMat = new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffffcc });
        
        const leftLight = new THREE.Mesh(lightGeo, lightMat);
        leftLight.position.set(-0.6, 0.7, -2);
        carGroup.add(leftLight);
        
        const rightLight = new THREE.Mesh(lightGeo, lightMat);
        rightLight.position.set(0.6, 0.7, -2);
        carGroup.add(rightLight);
        
        // Taillights
        const tailGeo = new THREE.BoxGeometry(0.3, 0.2, 0.1);
        const tailMat = new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000 });
        
        const leftTail = new THREE.Mesh(tailGeo, tailMat);
        leftTail.position.set(-0.6, 0.7, 2);
        carGroup.add(leftTail);
        
        const rightTail = new THREE.Mesh(tailGeo, tailMat);
        rightTail.position.set(0.6, 0.7, 2);
        carGroup.add(rightTail);
        
        return carGroup;
    }

    reset(x, z) {
        this.mesh.position.set(x, 0.5, z);
        this.mesh.rotation.set(0, 0, 0);
        this.speed = 0;
        this.currentWaypoint = 0;
        this.currentCheckpoint = -1;
        this.lapsCompleted = 0;
        this.checkpointsPassed = [];
        this.stuckTimer = 0;
        this.recoveryMode = false;
    }

    update(dt, keys) {
        if (!keys || !this.isPlayer) return;
        
        // Acceleration
        if (keys['w'] || keys['arrowup']) {
            this.speed += this.acceleration * dt * 60;
        } else if (keys['s'] || keys['arrowdown']) {
            this.speed -= this.braking * dt * 60;
        } else {
            // Natural deceleration
            this.speed *= this.friction;
        }
        
        // Clamp speed
        this.speed = Math.max(-this.maxSpeed / 2, Math.min(this.maxSpeed, this.speed));
        
        // Steering (speed-dependent)
        const steerFactor = Math.abs(this.speed) / this.maxSpeed * this.handling;
        if (Math.abs(this.speed) > 0.1) {
            if (keys['a'] || keys['arrowleft']) {
                this.mesh.rotation.y += 0.03 * steerFactor;
            }
            if (keys['d'] || keys['arrowright']) {
                this.mesh.rotation.y -= 0.03 * steerFactor;
            }
        }
        
        // Move car
        const moveDist = this.speed * dt;
        this.mesh.position.x += Math.sin(this.mesh.rotation.y) * moveDist;
        this.mesh.position.z -= Math.cos(this.mesh.rotation.y) * moveDist;
    }

    updateAI(dt, waypoints, playerCar, allCars) {
        if (!waypoints || waypoints.length === 0) return;
        
        // Get current target waypoint
        const target = waypoints[this.currentWaypoint];
        const carPos = this.mesh.position;
        
        // Calculate direction to target
        const dx = target.x - carPos.x;
        const dz = target.z - carPos.z;
        const distToTarget = Math.sqrt(dx * dx + dz * dz);
        const targetAngle = Math.atan2(dx, dz);
        
        // Smooth rotation towards target
        let angleDiff = targetAngle - this.mesh.rotation.y;
        while (angleDiff > Math.PI) angleDiff -= Math.PI * 2;
        while (angleDiff < -Math.PI) angleDiff += Math.PI * 2;
        
        const turnSpeed = 0.05 * this.handling;
        if (Math.abs(angleDiff) > turnSpeed) {
            this.mesh.rotation.y += Math.sign(angleDiff) * turnSpeed;
        } else {
            this.mesh.rotation.y = targetAngle;
        }
        
        // Adjust speed for corners
        const nextWaypoint = waypoints[(this.currentWaypoint + 1) % waypoints.length];
        const distToNext = Math.sqrt(
            (nextWaypoint.x - carPos.x) ** 2 + 
            (nextWaypoint.z - carPos.z) ** 2
        );
        
        // Slow down for tight corners
        let targetSpeed = this.maxSpeed;
        if (distToTarget < 30) {
            targetSpeed *= 0.6;
        }
        
        // Avoid other cars
        const avoidSpeed = this.avoidOtherCars(allCars, targetSpeed);
        targetSpeed = Math.min(targetSpeed, avoidSpeed);
        
        // Accelerate or brake towards target speed
        if (this.speed < targetSpeed) {
            this.speed += this.acceleration * dt * 60;
        } else {
            this.speed -= this.braking * dt * 60;
        }
        
        // Move car
        const moveDist = this.speed * dt;
        this.mesh.position.x += Math.sin(this.mesh.rotation.y) * moveDist;
        this.mesh.position.z -= Math.cos(this.mesh.rotation.y) * moveDist;
        
        // Check if we've reached the waypoint
        if (distToTarget < 15) {
            this.currentWaypoint = (this.currentWaypoint + 1) % waypoints.length;
            
            // Check for lap completion
            if (this.currentWaypoint === 0 && this.checkpointsPassed.length > 0) {
                this.lapsCompleted++;
                this.checkpointsPassed = [];
            }
        }
        
        // Recovery from being stuck
        if (Math.abs(this.speed) < 1 && distToTarget > 50) {
            this.stuckTimer += dt;
            if (this.stuckTimer > 2) {
                // Nudge forward
                this.speed = 10;
                this.stuckTimer = 0;
            }
        } else {
            this.stuckTimer = 0;
        }
    }

    avoidOtherCars(allCars, currentSpeed) {
        let minDist = Infinity;
        const carPos = this.mesh.position;
        
        allCars.forEach(other => {
            if (other === this) return;
            const dist = carPos.distanceTo(other.mesh.position);
            if (dist < 10 && dist < minDist) {
                minDist = dist;
            }
        });
        
        // Slow down if too close to another car
        if (minDist < 5) {
            return currentSpeed * 0.3;
        } else if (minDist < 8) {
            return currentSpeed * 0.6;
        }
        
        return currentSpeed;
    }

    updateCheckpoints(checkpoints) {
        if (!checkpoints || checkpoints.length === 0) return;
        
        const carPos = this.mesh.position;
        
        // Check if we've passed the next checkpoint
        for (let i = 0; i < checkpoints.length; i++) {
            const cp = checkpoints[i];
            const dist = Math.sqrt(
                (carPos.x - cp.x) ** 2 + 
                (carPos.z - cp.z) ** 2
            );
            
            if (dist < cp.radius && i === this.currentCheckpoint + 1) {
                this.currentCheckpoint = i;
                this.checkpointsPassed.push(i);
                
                // Check if lap is complete
                if (i === checkpoints.length - 1) {
                    this.lapsCompleted++;
                    this.currentCheckpoint = -1;
                    this.checkpointsPassed = [];
                }
            }
        }
    }
}
