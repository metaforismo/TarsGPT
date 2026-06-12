// TarsGPT — interactive exploded view of the no-arms TARS build.
// A stylized procedural model (boxes + brushed metal) matching the real
// V3-style robot: two outer leg slabs, a torso core with the electronics,
// and the center lift foot that makes the pivot gait work.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const stage = document.getElementById("stage");
const tooltip = document.getElementById("tooltip");
const partsList = document.getElementById("partsList");
const partDesc = document.getElementById("partDesc");
const explodeSlider = document.getElementById("explode");
const spinBox = document.getElementById("spin");

// ---------- renderer / scene ----------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
stage.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b10);
scene.fog = new THREE.Fog(0x070b10, 9, 18);

const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 60);
camera.position.set(3.4, 1.6, 4.6);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.1, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.1;
controls.maxDistance = 12;
controls.minDistance = 2;

scene.add(new THREE.HemisphereLight(0xbfdcff, 0x10141a, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
key.position.set(4, 6, 5);
scene.add(key);
const rim = new THREE.DirectionalLight(0x62d0ff, 0.7);
rim.position.set(-5, 2, -4);
scene.add(rim);

// floor grid + starfield
const grid = new THREE.GridHelper(20, 40, 0x16344a, 0x0d1b26);
grid.position.y = -1.32;
scene.add(grid);
{
  const positions = [];
  for (let i = 0; i < 500; i++) {
    const r = 14 + Math.random() * 10, t = Math.random() * Math.PI * 2,
          p = Math.acos(2 * Math.random() - 1);
    positions.push(r * Math.sin(p) * Math.cos(t), Math.abs(r * Math.cos(p)) - 2,
                   r * Math.sin(p) * Math.sin(t));
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  scene.add(new THREE.Points(geometry,
    new THREE.PointsMaterial({ color: 0x7fb6cc, size: 0.035, sizeAttenuation: true })));
}

// ---------- materials ----------
const M = {
  steel:  new THREE.MeshStandardMaterial({ color: 0xb9bec6, metalness: 0.9, roughness: 0.32 }),
  steel2: new THREE.MeshStandardMaterial({ color: 0x9aa1aa, metalness: 0.9, roughness: 0.38 }),
  dark:   new THREE.MeshStandardMaterial({ color: 0x23262b, metalness: 0.6, roughness: 0.5 }),
  groove: new THREE.MeshStandardMaterial({ color: 0x14171c, metalness: 0.5, roughness: 0.7 }),
  pcbG:   new THREE.MeshStandardMaterial({ color: 0x176d3f, metalness: 0.2, roughness: 0.6 }),
  pcbB:   new THREE.MeshStandardMaterial({ color: 0x10408f, metalness: 0.2, roughness: 0.6 }),
  pcbP:   new THREE.MeshStandardMaterial({ color: 0x5b2d91, metalness: 0.2, roughness: 0.6 }),
  servo:  new THREE.MeshStandardMaterial({ color: 0x101216, metalness: 0.3, roughness: 0.55 }),
  horn:   new THREE.MeshStandardMaterial({ color: 0xd8d8d8, metalness: 0.7, roughness: 0.35 }),
  glass:  new THREE.MeshStandardMaterial({ color: 0x0a1620, metalness: 0.4, roughness: 0.15,
                                           emissive: 0x0a2c3d, emissiveIntensity: 0.5 }),
  cellD:  new THREE.MeshStandardMaterial({ color: 0x143a5e, metalness: 0.4, roughness: 0.5 }),
};

// ---------- model ----------
const robot = new THREE.Group();
scene.add(robot);
const parts = [];

function box(w, h, d, material) {
  return new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
}

// grooved slab: the segmented TARS panel look
function slab(w, h, d, material) {
  const group = new THREE.Group();
  group.add(box(w, h, d, material));
  for (const fy of [-0.25, 0, 0.25]) {
    const groove = box(w * 1.01, 0.02, d * 1.01, M.groove);
    groove.position.y = fy * h * 1.6;
    group.add(groove);
  }
  return group;
}

function servoBox() {
  const group = new THREE.Group();
  group.add(box(0.22, 0.2, 0.19, M.servo));
  const flange = box(0.3, 0.03, 0.19, M.servo);
  flange.position.y = 0.06;
  group.add(flange);
  const hornMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.05, 20), M.horn);
  hornMesh.rotation.z = Math.PI / 2;
  hornMesh.position.set(0.13, 0.04, 0);
  group.add(hornMesh);
  return group;
}

function addPart(object, { name, desc, pos, explode }) {
  object.position.set(...pos);
  object.userData = { name, desc,
    base: new THREE.Vector3(...pos), explode: new THREE.Vector3(...explode) };
  robot.add(object);
  parts.push(object);
  return object;
}

// --- chassis ---
addPart(slab(0.78, 2.3, 0.5, M.steel2), {
  name: "Torso core (chassis)",
  desc: "The printed central frame: holds the electronics tray, the lift mechanism and both leg pivots. ~1 kg of PETG, 20% gyroid infill.",
  pos: [0, 0, 0], explode: [0, 0, 0] });

addPart(slab(0.34, 2.3, 0.5, M.steel), {
  name: "Port leg",
  desc: "Left leg slab. The drive servo pitches it around the shoulder axis — it can only swing forward/back, which is why strafing is composed from turns.",
  pos: [-0.62, 0, 0], explode: [-1.7, 0, 0] });

addPart(slab(0.34, 2.3, 0.5, M.steel), {
  name: "Starboard leg",
  desc: "Right leg slab, mirrored. With TPU foot pads it grips smooth floors during the pivot gait.",
  pos: [0.62, 0, 0], explode: [1.7, 0, 0] });

addPart(box(0.3, 0.5, 0.34, M.steel2), {
  name: "Center foot (lift)",
  desc: "The third leg: a lift servo extends it down to raise the torso, then retracts fast — gravity drops TARS into the pivot 'bump' that drives the walk.",
  pos: [0, -1.05, 0], explode: [0, -1.3, 0] });

addPart(box(0.74, 0.7, 0.05, M.steel), {
  name: "Front hull panel",
  desc: "Removable access panel. This is the face you finish with metallic filament or Humbrol Metalcote for the brushed-steel movie look.",
  pos: [0, -0.55, 0.28], explode: [0, -0.4, 1.6] });

addPart(box(0.74, 2.24, 0.05, M.steel), {
  name: "Back hull panel",
  desc: "Rear cover: cable routing, power switch and the charging port live here.",
  pos: [0, 0, -0.28], explode: [0, 0, -1.7] });

// --- actuators ---
addPart(servoBox(), {
  name: "Lift servo (MG996R)",
  desc: "Drives the center foot through a crank. Raising the torso is servo-limited (~0.4 m/s); the drop is gravity-assisted — the asymmetry that makes the gait work.",
  pos: [0, -0.62, 0.05], explode: [0, -0.75, 0.95] });

addPart(servoBox(), {
  name: "Port drive servo (MG996R)",
  desc: "Pitches the left leg. ~11 kg·cm at the 6.2 V rail. Buy a spare: budget clones vary.",
  pos: [-0.28, 0.55, 0.05], explode: [-1.0, 0.75, 0.85] });

addPart(servoBox(), {
  name: "Starboard drive servo (MG996R)",
  desc: "Pitches the right leg, mirrored with the port servo by the PCA9685.",
  pos: [0.28, 0.55, 0.05], explode: [1.0, 0.75, 0.85] });

// --- electronics ---
{
  const pi = new THREE.Group();
  pi.add(box(0.5, 0.04, 0.34, M.pcbG));
  for (const [x, z] of [[-0.12, 0.04], [0.08, -0.06], [0.15, 0.08]]) {
    const chip = box(0.09, 0.045, 0.09, M.dark); chip.position.set(x, 0.04, z); pi.add(chip);
  }
  addPart(pi, {
    name: "Raspberry Pi 5 (8 GB)",
    desc: "The brain: runs the voice pipeline, the LLM client, the skills, the dashboard and the fall watchdog — all in one Python process.",
    pos: [0, 0.12, 0.06], explode: [0, 0.55, 1.35] });
}
addPart(box(0.4, 0.035, 0.16, M.pcbB), {
  name: "PCA9685 servo driver",
  desc: "16-channel PWM controller on I2C: turns the Pi's commands into servo pulses. Its V+ rail is fed 6.2 V by the buck converter — never 12 V.",
  pos: [0, -0.12, 0.06], explode: [0, 0.18, 1.55] });

addPart(box(0.55, 0.34, 0.22, M.cellD), {
  name: "12 V battery pack",
  desc: "Li-ion 3000 mAh. Powers the servo rail through the XL4015 buck and the Pi through a 5 V USB regulator. The INA260 watches its voltage.",
  pos: [0, -0.85, -0.1], explode: [0, -0.35, -1.5] });

addPart(box(0.26, 0.09, 0.18, M.pcbB), {
  name: "Buck converters",
  desc: "XL4015 set to exactly 6.2 V for the servos, plus a 5 V/6 A USB regulator for the Pi. The single most common build mistake lives here.",
  pos: [0.18, -0.4, -0.12], explode: [0.55, 0.05, -1.4] });

addPart(box(0.56, 0.36, 0.04, M.glass), {
  name: 'DSI display (5")',
  desc: "The onboard screen: runs the movie-style readout at /display — humor and honesty bars, power, core temp, and a waveform that pulses when TARS listens.",
  pos: [0, 0.78, 0.28], explode: [0, 1.05, 1.15] });

addPart(box(0.1, 0.08, 0.04, M.pcbG), {
  name: "Camera (OV5647)",
  desc: "Eyes: the look skill describes the scene via a multimodal LLM, and during gait training the camera measures how far TARS actually walked.",
  pos: [0, 1.05, 0.28], explode: [0, 1.45, 0.9] });

{
  const speaker = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.06, 24), M.dark);
  speaker.rotation.x = Math.PI / 2;
  addPart(speaker, {
    name: "Speaker (8 Ω 5 W)",
    desc: "TARS's voice, driven through a USB sound card: ElevenLabs, OpenAI TTS, local Piper or espeak — whatever the fallback chain picks.",
    pos: [-0.62, -0.7, 0.2], explode: [-1.35, -0.8, 0.7] });
}
addPart(box(0.12, 0.035, 0.09, M.pcbP), {
  name: "IMU (MPU-6050)",
  desc: "€3 of balance: detects falls (servos relax automatically), taxes wobbly gaits during training, and reports attitude in system_status.",
  pos: [0.2, 0.32, 0.06], explode: [0.7, 0.75, 1.25] });

// ---------- parts list UI ----------
const items = parts.map((part, i) => {
  const li = document.createElement("li");
  li.textContent = part.userData.name;
  li.onclick = () => select(i);
  partsList.appendChild(li);
  return li;
});

let selected = -1;
function select(i) {
  selected = i === selected ? -1 : i;
  items.forEach((li, k) => li.classList.toggle("active", k === selected));
  if (selected >= 0) {
    const { name, desc } = parts[selected].userData;
    partDesc.innerHTML = `<b>${name}</b><br>${desc}`;
  } else {
    partDesc.textContent = "Click a part in the scene or in this list.";
  }
  applyHighlight();
}

function setEmissive(object, on) {
  object.traverse(node => {
    if (node.isMesh) {
      node.material = node.material.clone();
      node.material.emissive = new THREE.Color(on ? 0x2a7d9e : 0x000000);
      node.material.emissiveIntensity = on ? 0.8 : 0;
    }
  });
}
let hovered = -1;
function applyHighlight() {
  parts.forEach((part, i) => setEmissive(part, i === selected || i === hovered));
}

// ---------- interaction ----------
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function pick(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(parts, true);
  if (!hits.length) return -1;
  let node = hits[0].object;
  while (node && !parts.includes(node)) node = node.parent;
  return parts.indexOf(node);
}

renderer.domElement.addEventListener("pointermove", event => {
  const i = pick(event);
  if (i !== hovered) { hovered = i; applyHighlight(); }
  if (i >= 0) {
    tooltip.style.display = "block";
    const rect = stage.getBoundingClientRect();
    tooltip.style.left = (event.clientX - rect.left + 14) + "px";
    tooltip.style.top = (event.clientY - rect.top - 8) + "px";
    tooltip.textContent = parts[i].userData.name;
    stage.style.cursor = "pointer";
  } else {
    tooltip.style.display = "none";
    stage.style.cursor = "grab";
  }
});
renderer.domElement.addEventListener("click", event => {
  const i = pick(event);
  if (i >= 0) select(i);
});

// explode + controls
let explodeTarget = 0, explodeNow = 0;
explodeSlider.addEventListener("input", () => { explodeTarget = explodeSlider.value / 100; });
spinBox.addEventListener("change", () => { controls.autoRotate = spinBox.checked; });
document.getElementById("resetBtn").onclick = () => {
  explodeSlider.value = 0; explodeTarget = 0;
  camera.position.set(3.4, 1.6, 4.6);
  controls.target.set(0, 0.1, 0);
  select(-1);
};

// ---------- loop ----------
function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

renderer.setAnimationLoop(() => {
  explodeNow += (explodeTarget - explodeNow) * 0.08;
  for (const part of parts) {
    const { base, explode } = part.userData;
    part.position.set(base.x + explode.x * explodeNow,
                      base.y + explode.y * explodeNow,
                      base.z + explode.z * explodeNow);
  }
  controls.update();
  renderer.render(scene, camera);
});
