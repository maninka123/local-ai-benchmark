import * as THREE from 'three';

export class CarSelection {
  constructor() {
    this.element = document.createElement('div');
    this.element.style.position='absolute';
    this.element.style.top='10px';
    this.element.style.left='10px';
    this.element.style.background='rgba(0,0,0,0.5)';
    this.element.style.padding='10px';
    this.element.style.color='white';
    this.element.style.fontFamily='sans-serif';
    document.body.appendChild(this.element);
    this.onSelect = null;
    this.cars = [
      {name:'Speedster',color:0xff0000,maxSpeed:12,acceleration:6,braking:9,handling:0.07},
      {name:'Cruiser',color:0x00ff00,maxSpeed:10,acceleration:5,braking:8,handling:0.05},
      {name:'Racer',color:0x0000ff,maxSpeed:14,acceleration:7,braking:10,handling:0.09}
    ];
  }
  show(){
    this.element.innerHTML='Select Car:';
    this.cars.forEach((c,i)=>{
      const btn=document.createElement('button');
      btn.textContent=c.name;
      btn.style.margin='5px';
      btn.onclick=()=>{this.onSelect&&this.onSelect(c);};
      this.element.appendChild(btn);
    });
  }
}

export class HUD {
  constructor(){
    this.element=document.createElement('div');
    this.element.style.position='absolute';
    this.element.style.bottom='10px';
    this.element.style.left='10px';
    this.element.style.background='rgba(0,0,0,0.5)';
    this.element.style.padding='10px';
    this.element.style.color='white';
    this.element.style.fontFamily='sans-serif';
    document.body.appendChild(this.element);
    this.speed=0;this.lap=1;this.position=1;this.time=0;this.camera='Chase';
  }
  update(){
    this.element.innerHTML=`Speed: ${this.speed.toFixed(1)}<br>`+
      `Lap: ${this.lap}<br>`+
      `Position: ${this.position}<br>`+
      `Time: ${this.time.toFixed(1)}s<br>`+
      `Camera: ${this.camera}`;
  }
}
