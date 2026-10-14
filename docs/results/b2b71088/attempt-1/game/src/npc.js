class NPC extends Car {
  constructor(name) {
    super(name);
    this.targetAngle = 0;
  }
  update(delta) {
    // simple steering toward track direction
    super.update(delta);
  }
}
