import * as THREE from 'three';

export class Track {
    constructor(scene) {
        this.scene = scene;
        this.waypoints = [];
        this.checkpoints = [];
        this.createTrack();
    }

    createTrack() {
        this.createGround();
        this.createRoad();
        this.createBarriers();
        this.createScenery();
        this.createStartFinishLine();
        this.setupCheckpoints();
    }

    createGround() {
        const groundGeo = new THREE.PlaneGeometry(500, 500);
        const groundMat = new THREE.MeshStandardMaterial({ color: 0x2d5a27 });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    createRoad() {
        const roadWidth = 12;
        const segments = [];
        const curvePoints = [
            { x: 0, z: 0 },
            { x: 30, z: -50 },
            { x: 80, z: -80 },
            { x: 120, z: -60 },
            { x: 150, z: -20 },
            { x: 140, z: 30 },
            { x: 100, z: 70 },
            { x: 40, z: 90 },
            { x: -20, z: 80 },
            { x: -60, z: 50 },
            { x: -80, z: 10 },
            { x: -70, z: -30 },
            { x: -40, z: -50 },
            { x: -10, z: -60 },
            { x: 20, z: -50 }
        ];
        this.waypoints = curvePoints;
        for (let i = 0; i < curvePoints.length - 1; i++) {
            const p1 = curvePoints[i];
            const p2 = curvePoints[i + 1];
            const dx = p2.x - p1.x;
            const dz = p2.z - p1.z;
            const length = Math.sqrt(dx * dx + dz * dz);
            const angle = Math.atan2(dx, dz);
            const segGeo = new THREE.PlaneGeometry(roadWidth, length);
            const segMat = new THREE.MeshStandardMaterial({ color: 0x3a3a3a });
            const segment = new THREE.Mesh(segGeo, segMat);
            segment.rotation.x = -Math.PI / 2;
            segment.position.set((p1.x + p2.x) / 2, 0.05, (p1.z + p2.z) / 2);
            segment.rotation.y = angle;
            segment.receiveShadow = true;
            this.scene.add(segment);
            segments.push(segment);
        }
        const lastP = curvePoints[curvePoints.length - 1];
        const firstP = curvePoints[0];
        const dx = firstP.x - lastP.x;
        const dz = firstP.z - lastP.z;
        const length = Math.sqrt(dx * dx + dz * dz);
        const angle = Math.atan2(dx, dz);
        const segGeo = new THREE.PlaneGeometry(roadWidth, length);
        const segMat = new THREE.MeshStandardMaterial({ color: 0x3a3a3a });
        const segment = new THREE.Mesh(segGeo, segMat);
        segment.rotation.x = -Math.PI / 2;
        segment.position.set((lastP.x + firstP.x) / 2, 0.05, (lastP.z + firstP.z) / 2);
        segment.rotation.y = angle;
        segment.receiveShadow = true;
        this.scene.add(segment);
    }

    createBarriers() {
        const barrierGeo = new THREE.BoxGeometry(1, 1.5, 4);
        const barrierMat = new THREE.MeshStandardMaterial({ color: 0xcc3333 });
        const positions = [
            { x: 82, z: -78 }, { x: 122, z: -58 }, { x: 152, z: -18 },
            { x: 142, z: 32 }, { x: 102, z: 72 }, { x: 42, z: 92 },
            { x: -22, z: 82 }, { x: -62, z: 52 }, { x: -82, z: 12 },
            { x: -72, z: -32 }, { x: -42, z: -52 }, { x: -12, z: -62 }
        ];
        positions.forEach(pos => {
            const barrier = new THREE.Mesh(barrierGeo, barrierMat);
            barrier.position.set(pos.x, 0.75, pos.z);
            barrier.castShadow = true;
            this.scene.add(barrier);
        });
    }

    createScenery() {
        const treeTrunkGeo = new THREE.CylinderGeometry(0.3, 0.5, 2, 8);
        const treeTrunkMat = new THREE.MeshStandardMaterial({ color: 0x4a3728 });
        const treeLeavesGeo = new THREE.ConeGeometry(2, 4, 8);
        const treeLeavesMat = new THREE.MeshStandardMaterial({ color: 0x228b22 });
        const sceneryPositions = [
            { x: -100, z: -50 }, { x: 180, z: -40 }, { x: 160, z: 50 },
            { x: 80, z: 120 }, { x: -30, z: 130 }, { x: -120, z: 60 },
            { x: -140, z: -20 }, { x: -50, z: -100 }, { x: 50, z: -100 }
        ];
        sceneryPositions.forEach(pos => {
            const trunk = new THREE.Mesh(treeTrunkGeo, treeTrunkMat);
            trunk.position.set(pos.x, 1, pos.z);
            trunk.castShadow = true;
            this.scene.add(trunk);
            const leaves = new THREE.Mesh(treeLeavesGeo, treeLeavesMat);
            leaves.position.set(pos.x, 4, pos.z);
            leaves.castShadow = true;
            this.scene.add(leaves);
        });
    }

    createStartFinishLine() {
        const lineGeo = new THREE.PlaneGeometry(12, 3);
        const canvas = document.createElement('canvas');
        canvas.width = 64; canvas.height = 16;
        const ctx = canvas.getContext('2d');
        for (let i = 0; i < 8; i++) {
            ctx.fillStyle = (i % 2 === 0) ? '#ffffff' : '#000000';
            ctx.fillRect(i * 8, 0, 8, 16);
        }
        const texture = new THREE.CanvasTexture(canvas);
        const lineMat = new THREE.MeshBasicMaterial({ map: texture });
        const line = new THREE.Mesh(lineGeo, lineMat);
        line.rotation.x = -Math.PI / 2;
        line.position.set(0, 0.1, 0);
        this.scene.add(line);
    }

    setupCheckpoints() {
        this.checkpoints = [
            { x: 80, z: -80, radius: 15 },
            { x: 120, z: -60, radius: 15 },
            { x: 150, z: -20, radius: 15 },
            { x: 140, z: 30, radius: 15 },
            { x: 100, z: 70, radius: 15 },
            { x: 40, z: 90, radius: 15 },
            { x: -20, z: 80, radius: 15 },
            { x: -60, z: 50, radius: 15 },
            { x: -80, z: 10, radius: 15 },
            { x: -70, z: -30, radius: 15 },
            { x: -40, z: -50, radius: 15 },
            { x: -10, z: -60, radius: 15 }
        ];
    }
}
