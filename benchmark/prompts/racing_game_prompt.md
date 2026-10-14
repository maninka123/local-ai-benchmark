You are an experienced professional game developer.

Create a complete, visually polished and playable 3D arcade racing game that runs in a modern desktop browser.

The finished game must allow a human player to select a car and race against computer-controlled opponents.

You are responsible for implementation, testing and debugging.

**A. Racing environment**

Create a complete closed-loop 3D circuit.

The track must contain:

- Multiple corners
- Straight sections
- Track boundaries
- Visible road surfaces
- Barriers
- Environmental scenery
- Starting and finishing line
- Checkpoints

Design the track so that cars can complete full laps.

**B. Car selection**

Implement a vehicle selection menu.

Provide at least three visually distinct cars.

Each car must have different:

- Maximum speed
- Acceleration
- Braking behavior
- Handling characteristics

The selected vehicle must be used during the race.

**C. Driving controls**

Implement keyboard controls:

- W / Up Arrow: Accelerate
- S / Down Arrow: Brake or reverse
- A / Left Arrow: Steer left
- D / Right Arrow: Steer right
- C: Change camera
- P or Escape: Pause/resume
- R: Restart

Driving must include acceleration, deceleration, steering response, friction and speed-dependent handling.

**D. NPC opponents**

Implement at least four computer-controlled vehicles.

NPC vehicles must:

- Follow the track.
- Navigate corners.
- Adjust speed.
- Avoid obstacles where feasible.
- Attempt overtaking when possible.
- Handle collisions.
- Recover from being blocked or displaced.
- Complete laps independently.

Do not simply animate NPC cars along a fixed path without meaningful interaction with the race environment.

**E. Collision detection**

Implement functional collision behavior.

Cars must not pass freely through:

- Other vehicles
- Track barriers
- Major environmental obstacles

Collisions should produce a visible arcade-style response.

Prevent cars from becoming permanently stuck wherever reasonably possible.

**F. Camera system**

Implement at least three camera views:

1. Third-person chase camera
2. First-person cockpit or hood camera
3. Overhead camera

Allow the player to switch views during a race.

Camera transitions should be usable and avoid clipping where practical.

**G. Race mechanics**

Implement:

- Starting countdown
- Three-lap races
- Checkpoint validation
- Lap timing
- Race positioning
- Finish detection
- Final standings
- Restart functionality

Prevent shortcuts from counting as valid laps.

**H. User interface**

Include:

- Main menu
- Car selection
- Race HUD
- Current speed
- Current lap
- Player position
- Race timer
- Camera indicator
- Pause/resume
- Results screen
- Control instructions

**I. Visual design**

Create a visually appealing game.

Use:

- 3D vehicle geometry
- Suitable materials
- Lighting and shadows
- Attractive environmental colors
- Road markings
- Trackside details
- Clear UI hierarchy

The game should look like a deliberate arcade racing experience, not a primitive technical demo.

Do not depend on externally downloaded proprietary assets.

You may create procedural geometry, textures and other original assets.

**J. Verification**

Before submitting:

- Run the development build.
- Fix compilation errors.
- Test the game in a browser.
- Verify movement controls.
- Verify car selection.
- Verify camera switching.
- Verify collisions.
- Verify lap tracking.
- Verify that NPCs can complete laps.

**K. Final outputs**

Provide:

```text
output/
├── game/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── screenshots/
│   ├── menu.png
│   ├── race_chase.png
│   ├── race_hood.png
│   └── race_overhead.png
└── implementation_report.md
```

The implementation report should explain the game architecture, controls, implemented features, known limitations and verification results.

The game must be runnable using the documented local commands.

Deliver the working application, not merely a design proposal.