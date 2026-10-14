import * as THREE from 'three';
import { TRACK_POINTS, CHECKPOINTS } from './constants.js';

export class Track {
    constructor() {
        this.curve = new THREE.CatmullRomCurve3(TRACK_POINTS, true);
        this.waypoints = TRACK_POINTS.slice(0, -1);
        this.mesh = null;
        this.barriers = [];
        this.checkpoints = CHECKPOINTS.map(p => new THREE.Mesh(
            new THREE.SphereGeometry(2),
            new THREE.MeshBasicMaterial({ color: 0xffff00, transparent: true, opacity: 0.5 })
        )).map(m => { m.position.copy(p); m.position.y = 1; return m; });
    }

    generate(scene) {
        // Track Surface
        const geometry = new THREE.TubeGeometry(this.curve, 100, 12, 8, true);
        const material = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.DoubleSide });
        this.mesh = new THREE.Mesh(geometry, material);
        this.mesh.rotation.x = Math.PI / 2;
        this.mesh.position.y = -11;
        scene.add(this.mesh);

        // Road Markings
        const lineGeom = new THREE.TubeGeometry(this.curve, 100, 0.3, 8, true);
        const lineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const line = new THREE.Mesh(lineGeom, lineMat);
        line.rotation.x = Math.PI / 2;
        line.position.y = -10.85;
        scene.add(line);

        // Barriers
        const barrierGeom = new THREE.TubeGeometry(this.curve, 100, 13, 8, true);
        const barrierMat = new THREE.MeshStandardMaterial({ color: 0xff0000, wireframe: true, transparent: true, opacity: 0.3 });
        const barrier = new THREE.Mesh(barrierGeom, barrierMat);
        barrier.rotation.x = Math.PI / 2;
        barrier.position.y = -11;
        scene.add(barrier);
        this.barriers.push(barrier);

        // Ground
        const groundGeom = new THREE.PlaneGeometry(2000, 2000);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x228B22 });
        const ground = new THREE.Mesh(groundGeom, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -12;
        scene.add(ground);

        this.checkpoints.forEach(cp => scene.add(cp));
    }
}
