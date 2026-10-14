export default class HUD {
  constructor() {
    this.speedEl = document.getElementById('speed');
    this.lapEl = document.getElementById('lap');
    this.posEl = document.getElementById('position');
  }
  update(player) {
    this.speedEl.textContent = Math.floor(player.speed * 3.6);
    this.lapEl.textContent = `Lap ${Math.min(player.lap || 0, 3)}`;
    this.posEl.textContent = `Pos ${player.positionInRace || '?'}`;
  }
}
