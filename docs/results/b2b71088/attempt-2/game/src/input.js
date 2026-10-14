export default class Input {
  constructor(car) {
    this.car = car;
    this.keys = {};
    window.addEventListener('keydown', e => this.keys[e.key] = true);
    window.addEventListener('keyup', e => this.keys[e.key] = false);
  }
  update() {
    const k = this.keys;
    if (k['w'] || k['ArrowUp']) this.car.speed = Math.min(this.car.maxSpeed, this.car.speed + this.car.acceleration);
    if (k['s'] || k['ArrowDown']) this.car.speed = Math.max(0, this.car.speed - this.car.braking);
    if (k['a'] || k['ArrowLeft']) this.car.rotation -= this.car.handling;
    if (k['d'] || k['ArrowRight']) this.car.rotation += this.car.handling;
    if (k['c']) this.car.switchCamera();
    if (k['p'] || k['Escape']) this.car.togglePause();
    if (k['r']) this.car.restart();
  }
}
