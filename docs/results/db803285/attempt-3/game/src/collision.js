import * as THREE from 'three';

export function checkCollisions(playerCar, npcCars, barriers) {
  const player = playerCar.mesh;
  
  // Check collision with NPC cars
  npcCars.forEach(npc => {
    const npcMesh = npc.mesh;
    
    // Simple distance-based collision detection
    const distance = player.position.distanceTo(npc.position);
    const minDistance = 2.5; // Collision threshold
    
    if (distance < minDistance) {
      // Calculate collision normal
      const normal = new THREE.Vector3()
        .subVectors(player.position, npc.position)
        .normalize();
      
      // Push cars apart
      const pushAmount = minDistance - distance;
      player.position.add(normal.multiplyScalar(pushAmount));
      npc.position.sub(normal.multiplyScalar(pushAmount));
      
      // Reduce velocities on collision
      player.velocity.multiplyScalar(0.8);
      npc.velocity.multiplyScalar(0.8);
    }
  });
  
  // Check collision with barriers
  barriers.forEach(barrier => {
    const distance = player.position.distanceTo(barrier.position);
    const minDistance = 2.0;
    
    if (distance < minDistance) {
      const normal = new THREE.Vector3()
        .subVectors(player.position, barrier.position)
        .normalize();
      
      const pushAmount = minDistance - distance;
      player.position.add(normal.multiplyScalar(pushAmount));
      
      // Reduce velocity on barrier collision
      player.velocity.multiplyScalar(0.7);
    }
  });
}
