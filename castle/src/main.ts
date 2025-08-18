import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

type Clickable = THREE.Object3D & { __clickType?: 'character' | 'balloon' };

const canvas = document.createElement('canvas');
document.body.appendChild(canvas);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
renderer.setClearColor(0x87ceeb, 1); // bright sky

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0xbcd7ff, 0.006);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
camera.position.set(-80, 60, 140);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 30;
controls.maxDistance = 500;
controls.maxPolarAngle = Math.PI * 0.49;

// Lighting
const hemi = new THREE.HemisphereLight(0xeaf6ff, 0x8ea2b2, 1.05);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff7e0, 1.6);
sun.position.set(120, 160, 60);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -200;
sun.shadow.camera.right = 200;
sun.shadow.camera.top = 200;
sun.shadow.camera.bottom = -200;
sun.shadow.normalBias = 0.02;
scene.add(sun);

// Mountain peak
const mountainGeometry = new THREE.ConeGeometry(160, 260, 8, 12);
const mountainMaterial = new THREE.MeshStandardMaterial({ color: 0x6f7d8d, roughness: 0.92, metalness: 0.04 });
const mountain = new THREE.Mesh(mountainGeometry, mountainMaterial);
mountain.rotation.z = 0.1;
mountain.position.set(0, -50, 0);
mountain.receiveShadow = true;
scene.add(mountain);

// Castle walls and towers
const castleRoot = new THREE.Group();
scene.add(castleRoot);

function createTower(radius = 6, height = 28): THREE.Mesh {
  const geo = new THREE.CylinderGeometry(radius, radius, height, 16);
  const mat = new THREE.MeshStandardMaterial({ color: 0xc2ccd7, roughness: 0.88 });
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = true; m.receiveShadow = true;
  const crenelGeo = new THREE.BoxGeometry(radius * 0.7, 2.4, 2.4);
  for (let i = 0; i < 10; i++) {
    const c = new THREE.Mesh(crenelGeo, mat);
    const a = (i / 10) * Math.PI * 2;
    c.position.set(Math.cos(a) * radius * 0.9, height * 0.5 + 1.2, Math.sin(a) * radius * 0.9);
    c.rotation.y = a;
    c.castShadow = true; c.receiveShadow = true;
    m.add(c);
  }
  return m;
}

function createWall(length = 40, height = 16, thickness = 4): THREE.Mesh {
  const geo = new THREE.BoxGeometry(length, height, thickness);
  const mat = new THREE.MeshStandardMaterial({ color: 0xcad3df, roughness: 0.9 });
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = true; m.receiveShadow = true;
  // Crenelations
  const crenelGeo = new THREE.BoxGeometry(2, 2, thickness + 0.6);
  for (let x = -length / 2 + 2; x <= length / 2 - 2; x += 4) {
    const c = new THREE.Mesh(crenelGeo, mat);
    c.position.set(x, height / 2 + 1.2, 0);
    c.castShadow = true; c.receiveShadow = true;
    m.add(c);
  }
  return m;
}

// Layout castle courtyard on a flattened saddle of the mountain
const plateau = new THREE.Mesh(
  new THREE.CylinderGeometry(90, 120, 6, 24),
  new THREE.MeshStandardMaterial({ color: 0x8b99ab, roughness: 0.98 })
);
plateau.position.y = 30;
plateau.receiveShadow = true;
castleRoot.add(plateau);

const towerPositions = [
  new THREE.Vector3(-60, 38, -60),
  new THREE.Vector3(60, 38, -60),
  new THREE.Vector3(60, 38, 60),
  new THREE.Vector3(-60, 38, 60),
];
const towers: THREE.Object3D[] = [];
for (const p of towerPositions) {
  const t = createTower();
  t.position.copy(p);
  castleRoot.add(t);
  towers.push(t);
  // Add conical roof
  const roof = new THREE.Mesh(
    new THREE.ConeGeometry(8, 10, 16),
    new THREE.MeshStandardMaterial({ color: 0x8b3a3a, roughness: 0.75, metalness: 0.05 })
  );
  roof.position.y = 28 * 0.5 + 6;
  roof.castShadow = true; roof.receiveShadow = true;
  t.add(roof);
  // Add mast and flag
  const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 8, 8), new THREE.MeshStandardMaterial({ color: 0x9aa4ad, metalness: 0.6, roughness: 0.4 }));
  mast.position.y = 28 * 0.5 + 10;
  mast.castShadow = true; mast.receiveShadow = true;
  t.add(mast);
  const flag = new THREE.Mesh(new THREE.PlaneGeometry(4, 2, 1, 1), new THREE.MeshStandardMaterial({ color: Math.random() > 0.5 ? 0xff3b3b : 0x3b74ff, side: THREE.DoubleSide, roughness: 0.7, metalness: 0.05 }));
  flag.position.set(2.5, mast.position.y + 2.5, 0);
  flag.rotation.y = Math.PI / 2;
  flag.castShadow = true; flag.receiveShadow = true;
  castleRoot.add(flag);
  (flag as any).userData.wavePhase = Math.random() * Math.PI * 2;
}

const walls: THREE.Mesh[] = [];
function connect(a: THREE.Vector3, b: THREE.Vector3) {
  const len = a.distanceTo(b);
  const wall = createWall(len, 16, 4);
  wall.position.copy(a).add(b).multiplyScalar(0.5);
  wall.position.y = 38;
  wall.rotation.y = Math.atan2(b.x - a.x, b.z - a.z);
  castleRoot.add(wall);
  walls.push(wall);
}
connect(towerPositions[0], towerPositions[1]);
connect(towerPositions[1], towerPositions[2]);
connect(towerPositions[2], towerPositions[3]);
connect(towerPositions[3], towerPositions[0]);

// Gatehouse
const gate = new THREE.Mesh(
  new THREE.BoxGeometry(18, 20, 8),
  new THREE.MeshStandardMaterial({ color: 0xc2ccd7 })
);
gate.position.set(0, 38, -60);
gate.castShadow = true; gate.receiveShadow = true;
castleRoot.add(gate);

// Portcullis inside gate
const portcullis = new THREE.Group();
for (let x = -7; x <= 7; x += 2) {
  const bar = new THREE.Mesh(new THREE.BoxGeometry(0.5, 14, 0.5), new THREE.MeshStandardMaterial({ color: 0x44494f, metalness: 0.5, roughness: 0.6 }));
  bar.position.set(x, 38, -60 + 3.6);
  bar.castShadow = true; bar.receiveShadow = true;
  portcullis.add(bar);
}
castleRoot.add(portcullis);

// Keep
const keep = new THREE.Mesh(
  new THREE.BoxGeometry(28, 28, 28),
  new THREE.MeshStandardMaterial({ color: 0xb7c2cd, roughness: 0.84 })
);
keep.position.set(0, 50, 10);
keep.castShadow = true; keep.receiveShadow = true;
castleRoot.add(keep);
// Keep roof
const keepRoof = new THREE.Mesh(new THREE.ConeGeometry(16, 10, 4), new THREE.MeshStandardMaterial({ color: 0x7d2e2e, roughness: 0.78 }));
keepRoof.position.set(0, 50 + 14, 10);
keepRoof.castShadow = true; keepRoof.receiveShadow = true;
castleRoot.add(keepRoof);

// People and horses: simple animated instanced meshes for bustle
const peopleGeo = new THREE.CapsuleGeometry(0.7, 1.4, 4, 8);
const peopleMat = new THREE.MeshStandardMaterial({ color: 0xdec2a3 });
const people = new THREE.InstancedMesh(peopleGeo, peopleMat, 40);
people.castShadow = true; people.receiveShadow = true;
castleRoot.add(people);

const horseGeo = new THREE.BoxGeometry(2.2, 1.2, 4);
const horseMat = new THREE.MeshStandardMaterial({ color: 0x5a4633 });
const horses = new THREE.InstancedMesh(horseGeo, horseMat, 10);
horses.castShadow = true; horses.receiveShadow = true;
castleRoot.add(horses);

const rand = (min: number, max: number) => min + Math.random() * (max - min);
const tempObj = new THREE.Object3D();
const crowdWaypoints = [
  new THREE.Vector3(-30, 38, -20),
  new THREE.Vector3(30, 38, -10),
  new THREE.Vector3(25, 38, 30),
  new THREE.Vector3(-25, 38, 25),
];
const personPhase: number[] = [];
for (let i = 0; i < people.count; i++) {
  const p = crowdWaypoints[Math.floor(Math.random() * crowdWaypoints.length)].clone();
  p.x += rand(-10, 10); p.z += rand(-10, 10);
  tempObj.position.copy(p);
  tempObj.scale.setScalar(rand(0.8, 1.2));
  tempObj.updateMatrix();
  people.setMatrixAt(i, tempObj.matrix);
  personPhase.push(Math.random());
}
people.instanceMatrix.needsUpdate = true;

const horsePhase: number[] = [];
for (let i = 0; i < horses.count; i++) {
  const p = new THREE.Vector3(rand(-35, 35), 38, rand(-35, 35));
  tempObj.position.copy(p);
  tempObj.scale.setScalar(rand(0.9, 1.1));
  tempObj.updateMatrix();
  horses.setMatrixAt(i, tempObj.matrix);
  horsePhase.push(Math.random());
}
horses.instanceMatrix.needsUpdate = true;

// Patrols on walls with cannons
const patrolGeo = new THREE.CapsuleGeometry(0.7, 1.2, 4, 8);
const patrolMat = new THREE.MeshStandardMaterial({ color: 0x9f5454 });
const patrols = new THREE.InstancedMesh(patrolGeo, patrolMat, 20);
patrols.castShadow = true; patrols.receiveShadow = true;
castleRoot.add(patrols);

const pathCorners = towerPositions.map(p => new THREE.Vector3(p.x, 46, p.z));
const patrolPhase: number[] = [];
for (let i = 0; i < patrols.count; i++) {
  patrolPhase.push(Math.random());
}

// Cannons on corners
const cannonGeo = new THREE.CylinderGeometry(1.4, 1.4, 6, 8);
const cannonMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.6, roughness: 0.4 });
const cannons: THREE.Mesh[] = [];
for (const pos of towerPositions) {
  const base = new THREE.Mesh(new THREE.BoxGeometry(4, 2, 4), new THREE.MeshStandardMaterial({ color: 0x606060 }));
  base.position.set(pos.x, 46, pos.z);
  base.castShadow = true; base.receiveShadow = true;
  const barrel = new THREE.Mesh(cannonGeo, cannonMat);
  barrel.position.set(0, 2.5, 2.5);
  barrel.rotation.x = Math.PI / 2.4;
  barrel.castShadow = true; barrel.receiveShadow = true;
  const cannon = new THREE.Group();
  cannon.add(base); cannon.add(barrel);
  castleRoot.add(cannon);
  cannons.push(barrel);
}

// Balloons minigame
const balloonsGroup = new THREE.Group();
scene.add(balloonsGroup);
const balloonMat = new THREE.MeshStandardMaterial({ color: 0xff5e7e, roughness: 0.4, metalness: 0.15, emissive: 0x110006, emissiveIntensity: 0.3 });
function spawnBalloon() {
  const geo = new THREE.SphereGeometry(2.2, 16, 16);
  const mesh = new THREE.Mesh(geo, balloonMat.clone());
  mesh.castShadow = true; mesh.receiveShadow = true;
  mesh.position.set(rand(-70, 70), rand(46, 90), rand(-70, 70));
  (mesh as Clickable).__clickType = 'balloon';
  balloonsGroup.add(mesh);
}
for (let i = 0; i < 12; i++) spawnBalloon();

// Projectiles
const projectiles: { mesh: THREE.Mesh, velocity: THREE.Vector3, ttl: number }[] = [];
const projectileMat = new THREE.MeshStandardMaterial({ color: 0xf6d365, emissive: 0x553300, emissiveIntensity: 0.6 });
function shootProjectile(origin: THREE.Vector3, dir: THREE.Vector3) {
  const geo = new THREE.SphereGeometry(0.6, 12, 12);
  const mesh = new THREE.Mesh(geo, projectileMat);
  mesh.position.copy(origin);
  mesh.castShadow = true; mesh.receiveShadow = true;
  scene.add(mesh);
  projectiles.push({ mesh, velocity: dir.clone().multiplyScalar(140), ttl: 2.5 });
}

// Simple positional audio for hits
const listener = new THREE.AudioListener();
camera.add(listener);
const hitSound = new THREE.Audio(listener);
const audioCtx = (hitSound as any).context as AudioContext;
function playHitSound() {
  const o = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  o.type = 'triangle';
  o.frequency.setValueAtTime(880, audioCtx.currentTime);
  o.frequency.exponentialRampToValueAtTime(220, audioCtx.currentTime + 0.2);
  g.gain.setValueAtTime(0.0001, audioCtx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.2, audioCtx.currentTime + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.22);
  o.connect(g).connect(audioCtx.destination);
  o.start();
  o.stop(audioCtx.currentTime + 0.24);
}

// Dialogue system basics
type NPC = {
  id: string;
  name: string;
  mesh: Clickable;
};
const npcs: NPC[] = [];

function createNPC(name: string, position: THREE.Vector3): NPC {
  const group = new THREE.Group() as Clickable;
  group.position.copy(position);
  // Body with distinct attire
  const tunicColors = [0x3aaed8, 0x4caf50, 0xffb020, 0xbf5fff, 0xff5e7e];
  const body = new THREE.Mesh(
    new THREE.CapsuleGeometry(0.85, 1.8, 6, 12),
    new THREE.MeshStandardMaterial({ color: tunicColors[Math.floor(Math.random() * tunicColors.length)], roughness: 0.7, metalness: 0.05 })
  );
  body.castShadow = true; body.receiveShadow = true;
  group.add(body);
  // Head
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 12), new THREE.MeshStandardMaterial({ color: 0xffe0bd, roughness: 0.6 }));
  head.position.y = 1.6;
  head.castShadow = true; head.receiveShadow = true;
  group.add(head);
  // Click collider (larger, invisible)
  const collider = new THREE.Mesh(new THREE.SphereGeometry(1.4, 8, 8), new THREE.MeshBasicMaterial({ color: 0x00ff00, transparent: true, opacity: 0 }));
  collider.position.y = 1;
  (collider as Clickable).__clickType = 'character';
  group.add(collider);
  // Halo ring for visibility
  const halo = new THREE.Mesh(new THREE.RingGeometry(0.7, 1.15, 32), new THREE.MeshBasicMaterial({ color: 0xffd54f, transparent: true, opacity: 0.25, side: THREE.DoubleSide }));
  halo.rotation.x = -Math.PI / 2;
  halo.position.y = -0.9;
  group.add(halo);
  (group as any).userData.halo = halo;
  castleRoot.add(group);
  const id = `${name}_${Math.random().toString(36).slice(2, 7)}`;
  return { id, name, mesh: group };
}

const npcNames = ['Captain Aurelia', 'Stablemaster Tor', 'Cook Mila', 'Scribe Elian', 'Guard Niall', 'Mason Rhea', 'Herald Dori', 'Merchant Sava'];
for (let i = 0; i < npcNames.length; i++) {
  const npc = createNPC(npcNames[i], new THREE.Vector3(rand(-22, 22), 38, rand(-12, 26)));
  npcs.push(npc);
}

// Nameplates to indicate selected talk target
const nameplateEl = document.createElement('div');
nameplateEl.className = 'nameplate';
nameplateEl.style.display = 'none';
document.body.appendChild(nameplateEl);

// Dialogue UI hooks
const dialoguePanel = document.getElementById('dialoguePanel') as HTMLDivElement;
const dialogueName = document.getElementById('dialogueName') as HTMLSpanElement;
const dialogueLog = document.getElementById('dialogueLog') as HTMLDivElement;
const dialogueInput = document.getElementById('dialogueInput') as HTMLInputElement;
const dialogueSend = document.getElementById('dialogueSend') as HTMLButtonElement;
const dialogueClose = document.getElementById('dialogueClose') as HTMLButtonElement;

let currentTalk: NPC | null = null;
function openDialogue(npc: NPC) {
  currentTalk = npc;
  dialogueName.textContent = npc.name;
  dialoguePanel.classList.remove('hidden');
  dialogueLog.innerHTML = '';
  appendNpc(`Greetings, traveler. I am ${npc.name}.`);
  dialogueInput.focus();
}
function closeDialogue() {
  currentTalk = null;
  dialoguePanel.classList.add('hidden');
}
dialogueClose.addEventListener('click', closeDialogue);

function appendNpc(text: string) {
  const div = document.createElement('div');
  div.className = 'msg npc';
  div.textContent = text;
  dialogueLog.appendChild(div);
  dialogueLog.scrollTop = dialogueLog.scrollHeight;
}
function appendUser(text: string) {
  const div = document.createElement('div');
  div.className = 'msg user';
  div.textContent = text;
  dialogueLog.appendChild(div);
  dialogueLog.scrollTop = dialogueLog.scrollHeight;
}
function npcRespond(input: string): string {
  const key = input.toLowerCase();
  if (key.includes('hello') || key.includes('hi')) return 'Well met! The wind bites hard up here.';
  if (key.includes('castle')) return 'These walls have stood for centuries. The cannons are new, though.';
  if (key.includes('balloon')) return 'Balloons drifting over the keep? A curious festival, or a test of aim?';
  if (key.includes('horse')) return 'Our steeds are sure-footed on the cliffs. Treat them kindly.';
  if (key.includes('job') || key.includes('work')) return 'Keep watch, carry water, or test the cannons—there is always work.';
  return 'I will ponder that. The mountain keeps many secrets.';
}
function sendDialogue() {
  const text = dialogueInput.value.trim();
  if (!text) return;
  dialogueInput.value = '';
  appendUser(text);
  const reply = npcRespond(text);
  appendNpc(reply);
}
dialogueSend.addEventListener('click', sendDialogue);
dialogueInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendDialogue();
});

// Raycaster for clicks
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

// Scoreboard
const scoreValue = document.getElementById('scoreValue') as HTMLSpanElement;
let score = 0;
function addScore(n: number) {
  score += n; scoreValue.textContent = String(score);
}

// Handle clicks: shoot projectile; if character, open dialogue; if balloon, pop and score
function onClick(event: MouseEvent) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects([castleRoot, balloonsGroup], true);
  let targetPoint: THREE.Vector3 | null = null;
  for (const i of intersects) {
    const obj = i.object as Clickable;
    if (obj.__clickType === 'character') {
      const npc = npcs.find(n => n.mesh === obj || obj.parent === n.mesh);
      if (npc) {
        openDialogue(npc);
        targetPoint = i.point.clone();
        break;
      }
    } else if (obj.__clickType === 'balloon') {
      // Pop balloon
      balloonsGroup.remove(obj);
      obj.removeFromParent();
      addScore(10);
      playHitSound();
      targetPoint = i.point.clone();
      break;
    } else {
      targetPoint = i.point.clone();
      // continue searching in case a clickable is behind
    }
  }
  if (!targetPoint) {
    // shoot into the distance
    raycaster.ray.at(100, tempVec3);
    targetPoint = tempVec3.clone();
  }
  const origin = camera.position.clone();
  const dir = targetPoint.clone().sub(origin).normalize();
  shootProjectile(origin, dir);
}
renderer.domElement.addEventListener('click', onClick);

// Hover highlight for NPCs
let hoverNpc: NPC | null = null;
function onMouseMove(event: MouseEvent) {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const intersections = raycaster.intersectObjects([castleRoot], true);
  let found: NPC | null = null;
  for (const hit of intersections) {
    const obj = hit.object as Clickable;
    if (obj.__clickType === 'character') {
      const group = obj.parent as THREE.Object3D;
      const npc = npcs.find(n => n.mesh === group);
      if (npc) { found = npc; break; }
    }
  }
  hoverNpc = found;
  document.body.style.cursor = hoverNpc ? 'pointer' : 'default';
  // Update halos
  npcs.forEach(n => {
    const halo = (n.mesh as any).userData.halo as THREE.Mesh;
    const mat = halo.material as THREE.MeshBasicMaterial;
    mat.opacity = (n === hoverNpc || n === currentTalk) ? 0.9 : 0.15;
    mat.color.set(n === hoverNpc ? 0xfff176 : 0xffd54f);
  });
}
renderer.domElement.addEventListener('mousemove', onMouseMove);

// Clouds above
const clouds = new THREE.Group();
scene.add(clouds);
const cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0, transparent: true, opacity: 0.85 });
for (let i = 0; i < 30; i++) {
  const puff = new THREE.Mesh(new THREE.SphereGeometry(rand(8, 18), 12, 12), cloudMat.clone());
  puff.position.set(rand(-200, 200), rand(150, 220), rand(-200, 200));
  puff.rotation.y = Math.random() * Math.PI;
  clouds.add(puff);
}

// Cinematic camera path
let cinematicTime = 0;
let cinematic = true;
function toggleCinematic(on: boolean) {
  cinematic = on; controls.enabled = !on;
}
toggleCinematic(true);

// Helper vectors
const tempVec3 = new THREE.Vector3();

// Resize
window.addEventListener('resize', () => {
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h; camera.updateProjectionMatrix();
});

// Animate
const clock = new THREE.Clock();
function animate() {
  const dt = Math.min(0.033, clock.getDelta());

  // People wander
  for (let i = 0; i < people.count; i++) {
    const t = (personPhase[i] += dt * 0.1) % 1;
    const a = t * Math.PI * 2;
    const r = 18 + (i % 5);
    tempObj.position.set(Math.cos(a) * r, 38, Math.sin(a) * r * 0.6);
    tempObj.rotation.y = -a + Math.PI / 2;
    tempObj.updateMatrix();
    people.setMatrixAt(i, tempObj.matrix);
  }
  people.instanceMatrix.needsUpdate = true;

  // Horses loop
  for (let i = 0; i < horses.count; i++) {
    const t = (horsePhase[i] += dt * 0.06) % 1;
    const a = t * Math.PI * 2;
    const r = 28 + (i % 3) * 3;
    tempObj.position.set(Math.cos(a) * r, 38, Math.sin(a) * r);
    tempObj.rotation.y = -a + Math.PI / 2;
    tempObj.updateMatrix();
    horses.setMatrixAt(i, tempObj.matrix);
  }
  horses.instanceMatrix.needsUpdate = true;

  // Patrols around walls path
  for (let i = 0; i < patrols.count; i++) {
    const t = (patrolPhase[i] += dt * 0.03) % 1;
    const seg = Math.floor(t * 4);
    const lt = t * 4 - seg;
    const a = pathCorners[seg];
    const b = pathCorners[(seg + 1) % 4];
    tempObj.position.copy(a).lerp(b, lt);
    tempObj.position.y = 46;
    tempObj.lookAt(b.x, 46, b.z);
    tempObj.updateMatrix();
    patrols.setMatrixAt(i, tempObj.matrix);
  }
  patrols.instanceMatrix.needsUpdate = true;

  // Cannons occasionally fire
  if (Math.random() < dt * 0.5) {
    const cannon = cannons[Math.floor(Math.random() * cannons.length)];
    const worldPos = cannon.getWorldPosition(new THREE.Vector3());
    const forward = new THREE.Vector3(0, 1, 0).applyQuaternion(cannon.quaternion).normalize();
    shootProjectile(worldPos.addScaledVector(forward, 1.5), forward.add(new THREE.Vector3(rand(-0.05,0.05), rand(-0.05,0.05), rand(-0.05,0.05))).normalize());
  }

  // Balloons drift
  balloonsGroup.children.forEach((b, idx) => {
    b.position.x += Math.sin(clock.elapsedTime * 0.2 + idx) * 0.02;
    b.position.z += Math.cos(clock.elapsedTime * 0.18 + idx * 0.5) * 0.02;
    b.position.y += Math.sin(clock.elapsedTime * 0.5 + idx) * 0.01;
  });
  if (balloonsGroup.children.length < 12 && Math.random() < dt * 0.6) spawnBalloon();

  // Projectiles move and collide with balloons
  for (let i = projectiles.length - 1; i >= 0; i--) {
    const p = projectiles[i];
    p.ttl -= dt;
    p.mesh.position.addScaledVector(p.velocity, dt);
    p.velocity.y -= 9.8 * dt * 0.2;
    // Check collisions with balloons
    for (let j = balloonsGroup.children.length - 1; j >= 0; j--) {
      const b = balloonsGroup.children[j] as THREE.Mesh;
      if (p.mesh.position.distanceTo(b.position) < 2.4) {
        balloonsGroup.remove(b);
        b.removeFromParent();
        addScore(10);
        playHitSound();
        break;
      }
    }
    if (p.ttl <= 0) {
      scene.remove(p.mesh);
      projectiles.splice(i, 1);
    }
  }

  // Clouds drift slowly
  clouds.children.forEach((c, idx) => {
    c.position.x += 0.02 + Math.sin(clock.elapsedTime * 0.05 + idx) * 0.005;
  });

  // Flag waving animation
  castleRoot.children.forEach((child) => {
    if ((child as any).userData && (child as any).userData.wavePhase !== undefined && (child as THREE.Mesh).isMesh) {
      const flag = child as THREE.Mesh;
      const phase = (flag as any).userData.wavePhase as number;
      flag.rotation.z = Math.sin(clock.elapsedTime * 2 + phase) * 0.1;
    }
  });

  // Cinematic camera pan
  if (cinematic) {
    cinematicTime += dt * 0.2;
    const t = cinematicTime;
    const r = 180;
    camera.position.set(Math.cos(t) * r, 70 + Math.sin(t * 0.8) * 20, Math.sin(t) * r);
    camera.lookAt(0, 45, 0);
    if (cinematicTime > Math.PI * 2) toggleCinematic(false);
  } else {
    controls.update();
  }

  // Nameplate tracking for current talk target
  if (currentTalk) {
    const pos = currentTalk.mesh.getWorldPosition(new THREE.Vector3());
    pos.y += 3;
    pos.project(camera);
    const x = (pos.x * 0.5 + 0.5) * window.innerWidth;
    const y = (-pos.y * 0.5 + 0.5) * window.innerHeight;
    nameplateEl.style.left = `${x}px`;
    nameplateEl.style.top = `${y}px`;
    nameplateEl.textContent = currentTalk.name;
    nameplateEl.style.display = 'block';
  } else {
    nameplateEl.style.display = 'none';
  }

  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

// Allow user to re-enter cinematic by pressing C
window.addEventListener('keydown', (e) => {
  if (e.key.toLowerCase() === 'c') toggleCinematic(true);
});
