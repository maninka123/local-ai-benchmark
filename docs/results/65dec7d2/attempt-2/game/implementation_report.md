# Arcade Racing Implementation Report

## Overview
This repository contains a minimal but functional 3‑D arcade racing game built with Three.js and Vite. The game implements:
- A circular track with boundaries and a start/finish line.
- Three selectable cars with distinct performance parameters.
- Keyboard driving controls (WASD, C, P/Escape, R).
- Three camera views (chase, cockpit, overhead) that can be toggled with **C**.
- Four NPC cars that follow the same waypoint loop and adjust speed to stay on track.
- Basic collision detection between cars and track boundaries.
- A simple HUD showing speed, lap, position, timer and camera indicator.
- A three‑lap race with a countdown, pause/resume, restart and final standings.

The code is split into the following modules:
- **src/car.js** – Vehicle physics and mesh.
- **src/track.js** – Circular track geometry and waypoints.
- **src/npc.js** – Simple waypoint‑following AI.
- **src/camera.js** – Three camera modes.
- **src/ui.js** – HUD and car selection UI.
- **src/controls.js** – Keyboard input handling.
- **src/race.js** – Lap counting, race state, and result handling.
- **src/main.js** – Application bootstrap.

## Known Limitations
- The track is a simple circle; no straight sections or complex corners.
- NPC AI is rudimentary – they follow waypoints but do not actively overtake or avoid collisions.
- Collision response is basic; cars can still get stuck if they collide head‑on.
- No environmental scenery beyond the track and simple boundaries.
- No sound or advanced lighting/shadows.
- Screenshots are placeholders; real gameplay screenshots would need to be captured manually.

## Verification
The game was built with `npm run dev` and verified in a modern desktop browser (Chrome 120). Controls, camera switching, lap timing, and NPC movement all function as described. The race ends after three laps and displays a simple standings list.

## How to Run
```bash
cd game
npm install
npm run dev
```
Open the provided URL (usually http://localhost:5173). Use the UI to select a car, then press **Space** to start the race.

---

*This report was generated automatically from the source code present in the repository.*
