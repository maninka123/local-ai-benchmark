# 3D Arcade Racing Game

This is a complete 3D arcade racing game built using modern web technologies. The game features a closed-loop circuit with multiple corners, straight sections, and track boundaries, allowing players to complete full laps.

## Features

- Three distinct cars with different performance characteristics
- Realistic driving physics with acceleration, deceleration, steering, and friction
- Four computer-controlled NPC opponents that follow the track and attempt overtaking
- Functional collision detection with visible arcade-style responses
- Three camera views: third-person chase, first-person hood, and overhead
- Complete race mechanics including starting countdown, three-lap races, and finish detection
- Comprehensive user interface with race HUD, results screen, and control instructions

## How to Play

1. Select your car from the main menu
2. Start the race and use the following controls:
   - W/Up Arrow: Accelerate
   - S/Down Arrow: Brake or reverse
   - A/Left Arrow: Steer left
   - D/Right Arrow: Steer right
   - C: Change camera
   - P or Escape: Pause/resume
   - R: Restart
3. Complete three laps to win the race

## Technical Details

- Built with Three.js for 3D rendering
- Uses Vite for development server and build process
- All assets are procedurally generated
- The game runs in any modern desktop browser

## Known Limitations

- The game uses procedural geometry and textures rather than pre-made assets
- The NPC AI is relatively simple and may not handle complex racing situations optimally
- The collision detection system may have some inaccuracies in high-speed scenarios
- The game does not include sound effects or music

## Development

The game was developed using a component-based architecture with separate modules for:
- Track generation
- Car models and physics
- NPC AI
- Camera system
- Race management
- User interface

All features were thoroughly tested to ensure they work as expected.