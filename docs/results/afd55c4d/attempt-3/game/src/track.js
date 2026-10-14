import * as THREE from 'three';

export class Track {
    constructor(scene) {
        this.scene = scene;
        this.waypoints = [];
        this.checkpoints = [];
        this.barriers = [];
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
        const groundGeo = new THREE.PlaneGeometry(400, 400);
        const groundMat = new THREE.MeshStandardMaterial({ 
            color: 0x3d6b35,
            roughness: 1.0
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.1;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    createRoad() {
        const roadWidth = 14;
        
        // Define track waypoints (closed loop circuit)
        this.waypoints = [
            { x: 0, z: 0 },           // Start/Finish line
            { x: 25, z: -40 },        // Straight to first corner
            { x: 60, z: -70 },        // First corner entry
            { x: 100, z: -80 },       // First corner apex
            { x: 130, z: -50 },       // First corner exit
            { x: 150, z: -10 },       // Straight section
            { x: 140, z: 40 },        // Second corner entry
            { x: 100, z: 80 },        // Second corner apex
            { x: 50, z: 100 },        // Second corner exit
            { x: -10, z: 90 },        // Third corner entry
            { x: -50, z: 60 },        // Third corner apex
            { x: -70, z: 20 },        // Third corner exit
            { x: -60, z: -20 },       // Fourth corner entry
            { x: -30, z: -45 },       // Fourth corner apex
            { x: 0, z: -50 }          // Back to start straight
        ];
        
        const roadMat = new THREE.MeshStandardMaterial({ 
            color: 0x4a4a4a,
            roughness: 0.8
        });
        
        // Create road segments between waypoints
        for (let i = 0; i < this.waypoints.length; i++) {
            const p1 = this.waypoints[i];
            const p2 = this.waypoints[(i + 1) % this.waypoints.length];
            
            const dx = p2.x - p1.x;
            const dz = p2.z - p1.z;
            const length = Math.sqrt(dx * dx + dz * dz);
            const angle = Math.atan2(dx, dz);
            
            // Main road surface
            const segGeo = new THREE.PlaneGeometry(roadWidth, length);
            const segment = new THREE.Mesh(segGeo, roadMat);
            segment.rotation.x = -Math.PI / 2;
            segment.position.set((p1.x + p2.x) / 2, 0.02, (p1.z + p2.z) / 2);
            segment.rotation.y = angle;
            segment.receiveShadow = true;
            this.scene.add(segment);
            
            // Road markings (center line)
            const markingGeo = new THREE.PlaneGeometry(0.3, length * 0.8);
            const markingMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
            const marking = new THREE.Mesh(markingGeo, markingMat);
            marking.rotation.x = -Math.PI / 2;
            marking.position.set((p1.x + p2.x) / 2, 0.03, (p1.z + p2.z) / 2);
            marking.rotation.y = angle;
            this.scene.add(marking);
            
            // Edge lines
            const edgeGeo = new THREE.PlaneGeometry(0.2, length);
            const edgeMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
            
            const leftEdge = new THREE.Mesh(edgeGeo, edgeMat);
            leftEdge.rotation.x = -Math.PI / 2;
            leftEdge.position.set(
                (p1.x + p2.x) / 2,
                0.03,
                (p1.z + p2.z) / 2
            );
            leftEdge.rotation.y = angle;
            leftEdge.position.x += Math.sin(angle) * roadWidth / 2;
            leftEdge.position.z -= Math.cos(angle) * roadWidth / 2;
            this.scene.add(leftEdge);
            
            const rightEdge = new THREE.Mesh(edgeGeo, edgeMat);
            rightEdge.rotation.x = -Math.PI / 2;
            rightEdge.position.set(
                (p1.x + p2.x) / 2,
                0.03,
                (p1.z + p2.z) / 2
            );
            rightEdge.rotation.y = angle;
            rightEdge.position.x -= Math.sin(angle) * roadWidth / 2;
            rightEdge.position.z += Math.cos(angle) * roadWidth / 2;
            this.scene.add(rightEdge);
        }
    }

    createBarriers() {
        const barrierGeo = new THREE.BoxGeometry(1.5, 1.2, 3);
        const barrierMat = new THREE.MeshStandardMaterial({ 
            color: 0xcc3333,
            roughness: 0.7
        });
        
        // Barrier positions around corners
        const barrierPositions = [
            { x: 105, z: -85 },   // Corner 1 outer
            { x: 155, z: -5 },    // Straight side
            { x: 145, z: 45 },    // Corner 2 outer
            { x: 95, z: 85 },     // Corner 2 inner
            { x: 45, z: 105 },    // Corner 3 outer
            { x: -15, z: 95 },    // Corner 3 side
            { x: -55, z: 65 },    // Corner 3 inner
            { x: -75, z: 25 },    // Corner 4 outer
            { x: -65, z: -25 },   // Corner 4 side
            { x: -35, z: -50 }    // Final corner
        ];
        
        this.barriers = [];
        barrierPositions.forEach(pos => {
            const barrier = new THREE.Mesh(barrierGeo, barrierMat);
            barrier.position.set(pos.x, 0.6, pos.z);
            barrier.castShadow = true;
            barrier.receiveShadow = true;
            this.scene.add(barrier);
            this.barriers.push(barrier);
        });
    }

    createScenery() {
        // Trees
        const treeTrunkGeo = new THREE.CylinderGeometry(0.3, 0.5, 2.5, 8);
        const treeTrunkMat = new THREE.MeshStandardMaterial({ color: 0x4a3728 });
        const treeLeavesGeo = new THREE.ConeGeometry(2.5, 5, 8);
        const treeLeavesMat = new THREE.MeshStandardMaterial({ color: 0x2d5a27 });
        
        const treePositions = [
            { x: -100, z: -50 }, { x: -120, z: 0 }, { x: -130, z: 50 },
            { x: -100, z: 100 }, { x: -50, z: 140 }, { x: 0, z: 150 },
            { x: 50, z: 140 }, { x: 100, z: 120 }, { x: 150, z: 100 },
            { x: 180, z: 50 }, { x: 190, z: 0 }, { x: 170, z: -50 },
            { x: 140, z: -100 }, { x: 80, z: -120 }, { x: 20, z: -130 },
            { x: -30, z: -120 }, { x: -80, z: -100 }
        ];
        
        treePositions.forEach(pos => {
            const trunk = new THREE.Mesh(treeTrunkGeo, treeTrunkMat);
            trunk.position.set(pos.x, 1.25, pos.z);
            trunk.castShadow = true;
            this.scene.add(trunk);
            
            const leaves = new THREE.Mesh(treeLeavesGeo, treeLeavesMat);
            leaves.position.set(pos.x, 4, pos.z);
            leaves.castShadow = true;
            this.scene.add(leaves);
        });
        
        // Buildings/structures
        const buildingGeo = new THREE.BoxGeometry(8, 6, 8);
        const buildingMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
        
        const buildingPositions = [
            { x: -150, z: -30 }, { x: 200, z: -30 }, { x: 180, z: 80 }
        ];
        
        buildingPositions.forEach(pos => {
            const building = new THREE.Mesh(buildingGeo, buildingMat);
            building.position.set(pos.x, 3, pos.z);
            building.castShadow = true;
            this.scene.add(building);
        });
        
        // Grandstand at start/finish
        const grandstandGeo = new THREE.BoxGeometry(20, 4, 8);
        const grandstandMat = new THREE.MeshStandardMaterial({ color: 0x6666cc });
        const grandstand = new THREE.Mesh(grandstandGeo, grandstandMat);
        grandstand.position.set(-15, 2, -10);
        grandstand.castShadow = true;
        this.scene.add(grandstand);
    }

    createStartFinishLine() {
        // Checkered pattern for start/finish line
        const lineGeo = new THREE.PlaneGeometry(14, 3);
        
        // Create checkered texture procedurally
        const canvas = document.createElement('canvas');
        canvas.width = 64;
        canvas.height = 16;
        const ctx = canvas.getContext('2d');
        
        for (let row = 0; row < 4; row++) {
            for (let col = 0; col < 16; col++) {
                ctx.fillStyle = ((row + col) % 2 === 0) ? '#ffffff' : '#000000';
                ctx.fillRect(col * 4, row * 4, 4, 4);
            }
        }
        
        const texture = new THREE.CanvasTexture(canvas);
        texture.magFilter = THREE.NearestFilter;
        
        const lineMat = new THREE.MeshStandardMaterial({ 
            map: texture,
            transparent: true
        });
        
        const startLine = new THREE.Mesh(lineGeo, lineMat);
        startLine.rotation.x = -Math.PI / 2;
        startLine.position.set(0, 0.04, 0);
        this.scene.add(startLine);
    }

    setupCheckpoints() {
        // Checkpoints must be passed in order to complete a lap
        // Each checkpoint is positioned near the corresponding waypoint
        this.checkpoints = [
            { x: 25, z: -40, radius: 15 },   // CP1: First straight
            { x: 100, z: -80, radius: 15 },  // CP2: Corner 1
            { x: 150, z: -10, radius: 15 },  // CP3: Second straight
            { x: 100, z: 80, radius: 15 },   // CP4: Corner 2
            { x: -10, z: 90, radius: 15 },   // CP5: Corner 3
            { x: -60, z: -20, radius: 15 },  // CP6: Corner 4
            { x: 0, z: -50, radius: 15 }     // CP7: Final straight (lap complete)
        ];
    }
}
