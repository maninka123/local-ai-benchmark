export const config = {
  npcCount: 4,
  checkpointInterval: 8,
  trackRadius: 200
};

export const carSpecs = [
  { name: 'Speedster', color: 0xff3333, maxSpeed: 1.5, acceleration: 0.08, braking: 0.12, handling: 0.9 },
  { name: 'Steady', color: 0x3366ff, maxSpeed: 1.2, acceleration: 0.06, braking: 0.10, handling: 1.0 },
  { name: 'Drifter', color: 0x33ff33, maxSpeed: 1.0, acceleration: 0.05, braking: 0.08, handling: 1.2 }
];

export const trackPoints = [
  { x: 0, z: -200 },
  { x: 200, z: -100 },
  { x: 200, z: 100 },
  { x: 0, z: 200 },
  { x: -200, z: 100 },
  { x: -200, z: -100 }
];
