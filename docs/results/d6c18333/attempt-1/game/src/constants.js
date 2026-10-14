import * as THREE from 'three';

export const TRACK_POINTS = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(100, 0, 50),
    new THREE.Vector3(150, 0, 150),
    new THREE.Vector3(100, 0, 250),
    new THREE.Vector3(0, 0, 300),
    new THREE.Vector3(-100, 0, 250),
    new THREE.Vector3(-150, 0, 150),
    new THREE.Vector3(-100, 0, 50),
    new THREE.Vector3(0, 0, 0)
];

export const CAR_TYPES = [
    { name: 'Speedster', color: 0xff0000, maxSpeed: 1.2, acceleration: 0.05, braking: 0.05, handling: 0.04 },
    { name: 'Tank', color: 0x00ff00, maxSpeed: 0.8, acceleration: 0.03, braking: 0.08, handling: 0.02 },
    { name: 'Drifter', color: 0x0000ff, maxSpeed: 1.0, acceleration: 0.04, braking: 0.04, handling: 0.06 }
];

export const CHECKPOINTS = [
    new THREE.Vector3(100, 0, 50),
    new THREE.Vector3(150, 0, 150),
    new THREE.Vector3(100, 0, 250),
    new THREE.Vector3(0, 0, 300),
    new THREE.Vector3(-100, 0, 250),
    new THREE.Vector3(-150, 0, 150),
    new THREE.Vector3(-100, 0, 50)
];
