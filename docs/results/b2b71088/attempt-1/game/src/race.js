export default class RaceManager {
  constructor(player, checkpoints) {
    this.player = player;
    this.checkpoints = checkpoints;
    this.lapCount = 0;
    this.totalLaps = 3;
    this.finished = false;
  }
  checkpointPassed(pos) {
    const cp = this.checkpoints[0];
    const distance = cp.position.distanceTo(pos);
    if (distance < 5) {
      this.checkpoints.shift();
      this.lapCount++;
      if (this.lapCount >= this.totalLaps) this.finish();
    }
  }
  finish() { this.finished = true; }
  isFinished() { return this.finished; }
}
