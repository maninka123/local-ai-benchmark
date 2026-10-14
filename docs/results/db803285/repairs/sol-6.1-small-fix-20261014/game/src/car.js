import * as THREE from 'three';
import { config, carSpecs } from './config.js';

export function createCar(spec) {
  const carGroup = new THREE.Group();
  
  // Main body - different shapes for each car type
  let bodyGeometry;
  if (spec.name === 'Speedster') {
    // Sleek, low profile
    bodyGeometry = new THREE.BoxGeometry(2.2, 0.8, 4.5);
  } else if (spec.name === 'Steady') {
    // Balanced proportions
    bodyGeometry = new THREE.BoxGeometry(2.0, 1.0, 4.0);
  } else {
    // Drifter - wider stance
    bodyGeometry = new THREE.BoxGeometry(2.4, 0.9, 4.2);
  }
  
  const bodyMaterial = new THREE.MeshStandardMaterial({ color: spec.color });
  const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
  body.position.y = 0.5;
  body.castShadow = true;
  carGroup.add(body);
  
  // Cabin
  const cabinGeometry = new THREE.BoxGeometry(
    spec.name === 'Drifter' ? 1.6 : 1.8,
    0.6,
    2
  );
  const cabinMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
  const cabin = new THREE.Mesh(cabinGeometry, cabinMaterial);
  cabin.position.set(0, 1.2, -0.5);
  carGroup.add(cabin);
  
  // Wheels
  const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
  const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x111111 });
  
  const positions = [
    { x: -1, z: 1.2 },
    { x: 1, z: 1.2 },
    { x: -1, z: -1.2 },
    { x: 1, z: -1.2 }
  ];
  
  positions.forEach(pos => {
    const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(pos.x, 0.4, pos.z);
    carGroup.add(wheel);
  });
  
  // Headlights
  const lightGeometry = new THREE.BoxGeometry(0.3, 0.2, 0.1);
  const lightMaterial = new THREE.MeshBasicMaterial({ color: 0xffffaa });
  const leftLight = new THREE.Mesh(lightGeometry, lightMaterial);
  leftLight.position.set(-0.6, 0.5, 2.01);
  carGroup.add(leftLight);
  
  const rightLight = new THREE.Mesh(lightGeometry, lightMaterial);
  rightLight.position.set(0.6, 0.5, 2.01);
  carGroup.add(rightLight);
  
  // Taillights
  const tailLightMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
  const leftTail = new THREE.Mesh(lightGeometry, tailLightMaterial);
  leftTail.position.set(-0.6, 0.5, -2.01);
  carGroup.add(leftTail);
  
  const rightTail = new THREE.Mesh(lightGeometry, tailLightMaterial);
  rightTail.position.set(0.6, 0.5, -2.01);
  carGroup.add(rightTail);
  
  return {
    mesh: carGroup,
    spec: spec,
    position: new THREE.Vector3(),
    velocity: new THREE.Vector3(),
    acceleration: spec.acceleration,
    maxSpeed: spec.maxSpeed,
    braking: spec.braking,
    handling: spec.handling,
    checkpointIndex: -1
  };
}
