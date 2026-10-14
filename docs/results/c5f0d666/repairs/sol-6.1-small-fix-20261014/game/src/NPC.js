import * as THREE from 'three';
import { Car } from './Car.js';

export class NPC {
  constructor(track, carType) {
    this.track = track;
    this.carType = carType;
    this.car = null;
    this.position = new THREE.Vector3(0, 0, 0);
    this.targetPosition = new THREE.Vector3(0, 0, 0);
    this.targetAngle = 0;
    this.speed = 0;
    this.velocity = new THREE.Vector3();
    this.maxSpeed = 0;
    this.acceleration = 0;
    this.brakeForce = 0;
    this.handling = 0;
    this.isMoving = false;
    this.isBraking = false;
    this.isReversing = false;
    this.lapCount = 0;
    this.currentLap = 0;
    this.checkpointCount = 0;
    this.isFinished = false;
    this.position.set(0, 0, 0);
    this.setupNPC();
  }

  setupNPC() {
    // Create car based on type
    this.car = new Car(this.carType);
    
    // Set car properties
    this.maxSpeed = this.car.maxSpeed;
    this.acceleration = this.car.accelerationRate;
    this.brakeForce = this.car.brakeForce;
    this.handling = this.car.handling;
    
    // Set initial position
    this.position.set(0, 0, 0);
    this.car.setPosition(this.position);
    
    // Set initial velocity
    this.speed = 0;
    this.velocity = new THREE.Vector3();
    
    // Set initial lap count
    this.lapCount = 0;
    
    // Set initial checkpoint count
    this.checkpointCount = 0;
    
    // Set initial position
    this.position.set(0, 0, 0);
    
    // Set initial finish status
    this.isFinished = false;
  }

  update(deltaTime) {
    // Update NPC position based on track
    this.updatePosition(deltaTime);
    
    // Update car velocity based on acceleration
    this.updateVelocity(deltaTime);
    
    // Update car position
    this.car.car.position.add(this.velocity.clone().multiplyScalar(deltaTime));
    
    // Update car rotation
    this.car.car.rotation.y = Math.atan2(this.velocity.x, this.velocity.z);
    
    // Check if NPC has completed a lap
    this.checkLapCompletion();
    
    // Check if NPC has finished the race
    this.checkFinish();
  }

  updatePosition(deltaTime) {
    // Update position based on track
    const trackLength = this.track.numSegments * 2 * Math.PI * this.track.trackRadius / this.track.numSegments;
    const trackPosition = this.position.x * 2 * Math.PI * this.track.trackRadius / this.track.numSegments;
    
    // Calculate target position
    this.targetPosition.x = this.position.x + this.speed * deltaTime;
    
    // Update position
    this.position.x = this.targetPosition.x;
    
    // Update target angle
    this.targetAngle = this.position.x * 2 * Math.PI / this.track.numSegments;
    
    // Update car position
    this.car.car.position.x = this.position.x;
    
    // Update car rotation
    this.car.car.rotation.y = Math.atan2(this.velocity.x, this.velocity.z);
  }

  updateVelocity(deltaTime) {
    // Calculate acceleration based on input
    let acceleration = 0;
    
    // Apply acceleration based on input
    if (this.isMoving) {
      acceleration = this.accelerationRate;
    } else if (this.isBraking) {
      acceleration = -this.brakeForce;
    } else if (this.isReversing) {
      acceleration = -this.accelerationRate;
    }
    
    // Apply acceleration to velocity
    this.velocity.x += acceleration * deltaTime;
    
    // Apply friction
    this.velocity.x *= 0.99;
    
    // Limit speed
    if (Math.abs(this.velocity.x) > this.maxSpeed) {
      this.velocity.x = this.maxSpeed * Math.sign(this.velocity.x);
    }
  }

  checkLapCompletion() {
    // Check if NPC has completed a lap
    if (this.checkpointCount >= 4) {
      this.lapCount++;
      this.currentLap = 1;
      this.checkpointCount = 0;
    }
  }

  checkFinish() {
    // Check if NPC has finished the race
    if (this.lapCount >= 3) {
      this.isFinished = true;
    }
  }

  getCar() {
    return this.car.getCar();
  }

  getVelocity() {
    return this.velocity;
  }

  getLapCount() {
    return this.lapCount;
  }

  getCheckpointCount() {
    return this.checkpointCount;
  }

  getPosition() {
    return this.position;
  }

  setPosition(position) {
    this.position.copy(position);
  }

  setMoving(moving) {
    this.isMoving = moving;
  }

  setBraking(braking) {
    this.isBraking = braking;
  }

  setReversing(reversing) {
    this.isReversing = reversing;
  }

  setAcceleration(acceleration) {
    this.acceleration = acceleration;
  }

  setMaxSpeed(maxSpeed) {
    this.maxSpeed = maxSpeed;
  }

  setAccelerationRate(accelerationRate) {
    this.accelerationRate = accelerationRate;
  }

  setBrakeForce(brakeForce) {
    this.brakeForce = brakeForce;
  }

  setHandling(handling) {
    this.handling = handling;
  }

  setCar(car) {
    this.car = car;
  }

  setCheckpointCount(checkpointCount) {
    this.checkpointCount = checkpointCount;
  }

  setFinished(isFinished) {
    this.isFinished = isFinished;
  }
}