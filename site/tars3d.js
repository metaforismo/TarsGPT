// TarsGPT — cinematic interactive model of the no-arms TARS build.
// Dark gunmetal slabs with rounded edges and segment gaps (movie-style),
// a live green terminal screen rendered to a CanvasTexture, vertical TARS
// lettering, environment-lit PBR metal, soft shadows, and an exploded view
// of every real component in the build.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const stage = document.getElementById("stage");
const tooltip = document.getElementById("tooltip");
const partsList = document.getElementById("partsList");
const partCard = document.getElementById("partCard");
const explodeSlider = document.getElementById("explode");

// ---------- renderer / scene ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0b0d);
scene.fog = new THREE.Fog(0x0a0b0d, 10, 22);

// image-based lighting: this is what makes the metal read as metal
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 80);
const HOME = new THREE.Vector3(3.2, 1.15, 4.6);
camera.position.copy(HOME);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.05, 0);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.65;
controls.maxPolarAngle = Math.PI * 0.55;
// the page owns the wheel and vertical swipes; the robot owns drags -
// otherwise visitors get trapped in the canvas and can't scroll
controls.enableZoom = false;
renderer.domElement.style.touchAction = "pan-y";

const key = new THREE.DirectionalLight(0xfff4e0, 2.2);
key.position.set(5, 7, 4);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = key.shadow.camera.bottom = -4;
key.shadow.camera.right = key.shadow.camera.top = 4;
key.shadow.radius = 6;
scene.add(key);
const fill = new THREE.DirectionalLight(0x9ab8d0, 0.5);
fill.position.set(-6, 3, -5);
scene.add(fill);

// floor: soft real shadow only
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60),
  new THREE.ShadowMaterial({ opacity: 0.42 }));
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1.31;
floor.receiveShadow = true;
scene.add(floor);
const ring = new THREE.Mesh(new THREE.RingGeometry(2.4, 2.42, 96),
  new THREE.MeshBasicMaterial({ color: 0x2a2e33, side: THREE.DoubleSide }));
ring.rotation.x = -Math.PI / 2;
ring.position.y = -1.3;
scene.add(ring);

// ---------- materials (dark gunmetal, like the real prop) ----------
function metal(color, roughness = 0.42) {
  return new THREE.MeshStandardMaterial({ color, metalness: 0.78, roughness });
}
const M = {
  slab:   metal(0x43474d),
  slab2:  metal(0x383c42, 0.48),
  inset:  new THREE.MeshStandardMaterial({ color: 0x101214, metalness: 0.5, roughness: 0.6 }),
  screw:  metal(0x1b1d20, 0.35),
  pcbG:   new THREE.MeshStandardMaterial({ color: 0x14582f, metalness: 0.1, roughness: 0.55 }),
  pcbB:   new THREE.MeshStandardMaterial({ color: 0x0e3a7c, metalness: 0.1, roughness: 0.55 }),
  pcbP:   new THREE.MeshStandardMaterial({ color: 0x4a2578, metalness: 0.1, roughness: 0.55 }),
  servo:  new THREE.MeshStandardMaterial({ color: 0x0d0f12, metalness: 0.25, roughness: 0.5 }),
  horn:   metal(0xc9ccd1, 0.3),
  cell:   new THREE.MeshStandardMaterial({ color: 0x0f2a47, metalness: 0.3, roughness: 0.5 }),
};

function rbox(w, h, d, material, r = 0.025) {
  const mesh = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 3, r), material);
  mesh.castShadow = true;
  return mesh;
}

// ---------- live terminal screen (CanvasTexture) ----------
const TERM_LINES = [
  "TARSGPT OS · ENDURANCE — boot",
  "i2c: PCA9685 @0x40 ......... OK",
  "i2c: MPU-6050 @0x68 ........ OK",
  "servo rail ........... 6.20 V",
  "gait params ........... loaded",
  "humor ..................  75%",
  "honesty ................  90%",
  "sarcasm ................  30%",
  "wake word ............. \"tars\"",
  "fall watchdog .......... armed",
  "skills ................ 18/18",
  "cue light .............. on",
  "> awaiting instructions",
];
const termCanvas = document.createElement("canvas");
termCanvas.width = 512; termCanvas.height = 640;
const termCtx = termCanvas.getContext("2d");
const termTex = new THREE.CanvasTexture(termCanvas);
termTex.colorSpace = THREE.SRGBColorSpace;
let termChars = 0;
function drawTerminal() {
  const c = termCtx;
  c.fillStyle = "#020503";
  c.fillRect(0, 0, 512, 640);
  c.font = "22px 'JetBrains Mono', monospace";
  c.fillStyle = "#39e16e";
  c.shadowColor = "#39e16e"; c.shadowBlur = 7;
  let budget = termChars, y = 44, cursorX = 26, cursorY = 44;
  for (const line of TERM_LINES) {
    if (budget <= 0) break;
    const shown = line.slice(0, budget);
    c.fillText(shown, 26, y);
    cursorX = 26 + c.measureText(shown).width + 6;
    cursorY = y;
    budget -= line.length;
    y += 46;
  }
  if (Math.floor(Date.now() / 450) % 2) c.fillRect(cursorX, cursorY - 18, 12, 22);
  c.shadowBlur = 0;
  c.fillStyle = "rgba(0,0,0,0.22)";              // scanlines
  for (let sy = 0; sy < 640; sy += 4) c.fillRect(0, sy, 512, 2);
  termTex.needsUpdate = true;
}
setInterval(() => {
  termChars = (termChars + 2) % (TERM_LINES.join("").length + 90);
  drawTerminal();
}, 90);
drawTerminal();

const screenMat = new THREE.MeshStandardMaterial({
  map: termTex, emissive: 0xffffff, emissiveMap: termTex,
  emissiveIntensity: 1.25, metalness: 0.1, roughness: 0.35,
});

// vertical amber "TARS" lettering
const nameCanvas = document.createElement("canvas");
nameCanvas.width = 96; nameCanvas.height = 512;
const nc = nameCanvas.getContext("2d");
nc.clearRect(0, 0, 96, 512);
nc.font = "700 76px 'Space Grotesk', sans-serif";
nc.fillStyle = "#e8b54a";
nc.textAlign = "center";
"TARS".split("").forEach((ch, i) => nc.fillText(ch, 48, 96 + i * 112));
const nameTex = new THREE.CanvasTexture(nameCanvas);
nameTex.colorSpace = THREE.SRGBColorSpace;
const nameMat = new THREE.MeshStandardMaterial({
  map: nameTex, transparent: true, metalness: 0.3, roughness: 0.5,
  emissive: 0xe8b54a, emissiveMap: nameTex, emissiveIntensity: 0.12,
});

// ---------- model ----------
const robot = new THREE.Group();
scene.add(robot);
const parts = [];

// a TARS slab: stacked rounded segments with hairline gaps (movie look)
function slab(w, totalH, d, material, segments = 4) {
  const group = new THREE.Group();
  const gap = 0.018;
  const segH = (totalH - gap * (segments - 1)) / segments;
  for (let i = 0; i < segments; i++) {
    const seg = rbox(w, segH, d, material, 0.03);
    seg.position.y = -totalH / 2 + segH / 2 + i * (segH + gap);
    group.add(seg);
  }
  return group;
}

function handleSlot(parent, y, z = 0) {
  const slot = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.07, 0.06), M.inset);
  slot.position.set(0, y, z);
  parent.add(slot);
}

function screwDots(parent, w, h, z) {
  for (const [sx, sy] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) {
    const screw = new THREE.Mesh(
      new THREE.CylinderGeometry(0.016, 0.016, 0.015, 12), M.screw);
    screw.rotation.x = Math.PI / 2;
    screw.position.set(sx * w / 2 * 0.86, sy * h / 2 * 0.86, z);
    parent.add(screw);
  }
}

function servoBox() {
  const group = new THREE.Group();
  group.add(rbox(0.22, 0.2, 0.19, M.servo, 0.015));
  const flange = rbox(0.3, 0.03, 0.19, M.servo, 0.008);
  flange.position.y = 0.065;
  group.add(flange);
  const horn = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.05, 20), M.horn);
  horn.rotation.z = Math.PI / 2;
  horn.position.set(0.13, 0.04, 0);
  horn.castShadow = true;
  group.add(horn);
  return group;
}

function addPart(object, { name, desc, pos, explode }) {
  object.position.set(...pos);
  object.userData = { name, desc,
    base: new THREE.Vector3(...pos), explode: new THREE.Vector3(...explode) };
  object.traverse(node => { if (node.isMesh) node.castShadow = true; });
  robot.add(object);
  parts.push(object);
  return object;
}

// --- torso: wide central slab, slightly taller (like the reference) ---
{
  const torso = new THREE.Group();
  torso.add(slab(0.8, 2.42, 0.5, M.slab2, 4));
  const crown = rbox(0.52, 0.1, 0.46, M.slab2, 0.025);   // raised top step
  crown.position.y = 1.26;
  torso.add(crown);
  screwDots(torso, 0.8, 2.3, 0.252);
  addPart(torso, {
    name: "Torso core (chassis)",
    desc: "The printed central frame: electronics tray, lift mechanism and both leg pivots. ~1 kg of PETG at 20% gyroid infill.",
    pos: [0, 0.06, 0], explode: [0, 0, 0] });
}

// --- outer legs ---
{
  const leg = slab(0.36, 2.3, 0.52, M.slab, 4);
  handleSlot(leg, 0.18, 0.27);
  addPart(leg, {
    name: "Port leg",
    desc: "Left leg slab. The drive servo pitches it around the shoulder axis — it only swings forward/back, which is why strafing is composed from turns.",
    pos: [-0.64, 0, 0], explode: [-1.8, 0, 0] });
}
{
  const leg = slab(0.36, 2.3, 0.52, M.slab, 4);
  handleSlot(leg, 0.18, 0.27);
  addPart(leg, {
    name: "Starboard leg",
    desc: "Right leg slab, mirrored. TPU foot pads give it grip on smooth floors during the pivot gait.",
    pos: [0.64, 0, 0], explode: [1.8, 0, 0] });
}

addPart(rbox(0.3, 0.5, 0.34, M.slab2, 0.03), {
  name: "Center foot (lift)",
  desc: "The third leg: the lift servo extends it to raise the torso, then retracts fast — gravity drops TARS into the pivot 'bump' that drives the walk.",
  pos: [0, -1.0, 0], explode: [0, -1.25, 0] });

// --- screen assembly on the torso front ---
{
  const display = new THREE.Group();
  const bezel = rbox(0.62, 0.78, 0.05, M.inset, 0.012);
  display.add(bezel);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(0.54, 0.7), screenMat);
  glass.position.z = 0.028;
  display.add(glass);
  addPart(display, {
    name: 'DSI display (5")',
    desc: "The onboard terminal: the movie-style readout at /display shows humor and honesty bars, power, core temp — and a waveform that pulses when TARS listens.",
    pos: [0.06, 0.62, 0.27], explode: [0.25, 0.95, 1.25] });
}
{
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(0.14, 0.74), nameMat);
  addPart(plate, {
    name: "Name plate",
    desc: "Every good robot signs its work. Painted amber on the finished build — Rub 'n Buff over a stencil works beautifully.",
    pos: [-0.31, 0.62, 0.282], explode: [-0.45, 0.95, 1.35] });
}

addPart(rbox(0.76, 0.92, 0.05, M.slab, 0.02), {
  name: "Front access panel",
  desc: "Removable lower panel. This is the face you finish for the brushed-metal movie look: metallic filament, or primer + Humbrol Metalcote, buffed.",
  pos: [0, -0.62, 0.265], explode: [0, -0.5, 1.7] });

addPart(rbox(0.76, 2.32, 0.05, M.slab, 0.02), {
  name: "Back hull panel",
  desc: "Rear cover: cable routing, the power switch and the charging port live here.",
  pos: [0, 0.05, -0.265], explode: [0, 0, -1.8] });

// --- actuators ---
addPart(servoBox(), {
  name: "Lift servo (MG996R)",
  desc: "Drives the center foot through a crank. Raising the torso is servo-limited (~0.4 m/s); the drop is gravity-assisted — the asymmetry that makes the gait work.",
  pos: [0, -0.55, 0.05], explode: [0, -0.85, 1.0] });
addPart(servoBox(), {
  name: "Port drive servo (MG996R)",
  desc: "Pitches the left leg. ~11 kg·cm on the 6.2 V rail. Buy a spare — budget clones vary.",
  pos: [-0.28, 0.95, 0.05], explode: [-1.05, 0.8, 0.95] });
addPart(servoBox(), {
  name: "Starboard drive servo (MG996R)",
  desc: "Pitches the right leg, mirrored with the port servo by the PCA9685.",
  pos: [0.28, 0.95, 0.05], explode: [1.05, 0.8, 0.95] });

// --- electronics ---
{
  const pi = new THREE.Group();
  pi.add(rbox(0.5, 0.04, 0.34, M.pcbG, 0.008));
  for (const [x, z] of [[-0.12, 0.04], [0.08, -0.06], [0.15, 0.08]]) {
    const chip = rbox(0.09, 0.045, 0.09, M.inset, 0.006);
    chip.position.set(x, 0.04, z);
    pi.add(chip);
  }
  addPart(pi, {
    name: "Raspberry Pi 5 (8 GB)",
    desc: "The brain: voice pipeline, LLM client, 18 skills, dashboard and fall watchdog — one Python process.",
    pos: [0, 0.18, 0.02], explode: [0, 0.5, 1.5] });
}
addPart(rbox(0.4, 0.035, 0.16, M.pcbB, 0.008), {
  name: "PCA9685 servo driver",
  desc: "16-channel PWM on I2C: turns the Pi's commands into servo pulses. Its V+ rail gets exactly 6.2 V — never 12.",
  pos: [0, -0.08, 0.02], explode: [0, 0.12, 1.65] });
addPart(rbox(0.55, 0.34, 0.22, M.cell, 0.025), {
  name: "12 V battery pack",
  desc: "Li-ion 3000 mAh feeding the servo rail and the Pi through separate regulators. The INA260 watches it; TARS announces when it runs low.",
  pos: [0, -1.0, -0.08], explode: [0, -0.4, -1.6] });
addPart(rbox(0.26, 0.09, 0.18, M.pcbB, 0.01), {
  name: "Buck converters",
  desc: "XL4015 trimmed to 6.2 V for the servos + a 5 V/6 A USB regulator for the Pi. The most common build mistake lives on this board.",
  pos: [0.18, -0.32, -0.1], explode: [0.6, 0.0, -1.5] });
addPart(rbox(0.1, 0.08, 0.05, M.pcbG, 0.008), {
  name: "Camera (OV5647)",
  desc: "Eyes: the look skill describes the scene through a multimodal LLM, and in gait training the camera measures how far TARS really walked.",
  pos: [0.06, 1.12, 0.27], explode: [0.1, 1.5, 1.0] });
{
  const speaker = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.13, 0.06, 28), M.inset);
  speaker.rotation.x = Math.PI / 2;
  speaker.castShadow = true;
  addPart(speaker, {
    name: "Speaker (8 Ω 5 W)",
    desc: "TARS's voice through a USB sound card: ElevenLabs, OpenAI TTS, local Piper or espeak — whatever the fallback chain picks.",
    pos: [-0.64, -0.7, 0.21], explode: [-1.45, -0.85, 0.75] });
}
addPart(rbox(0.12, 0.035, 0.09, M.pcbP, 0.008), {
  name: "IMU (MPU-6050)",
  desc: "€3 of balance: detects falls (servos relax automatically), taxes wobbly gaits during training, reports attitude on demand.",
  pos: [0.2, 0.4, 0.02], explode: [0.75, 0.65, 1.4] });

// ---------- UI: parts list + selection card ----------
const items = parts.map((part, i) => {
  const li = document.createElement("li");
  li.innerHTML = `<span>${String(i + 1).padStart(2, "0")}</span>${part.userData.name}`;
  li.onclick = () => select(i);
  partsList.appendChild(li);
  return li;
});

let selected = -1, hovered = -1;
function select(i) {
  selected = i === selected ? -1 : i;
  items.forEach((li, k) => li.classList.toggle("active", k === selected));
  if (selected >= 0) {
    const { name, desc } = parts[selected].userData;
    partCard.innerHTML = `<b>${name}</b><p>${desc}</p>`;
    partCard.classList.add("show");
  } else {
    partCard.classList.remove("show");
  }
  applyHighlight();
}
function setEmissive(object, on) {
  object.traverse(node => {
    if (node.isMesh && node.material !== screenMat && node.material !== nameMat) {
      if (!node.userData.ownMat) { node.material = node.material.clone(); node.userData.ownMat = true; }
      node.material.emissive = new THREE.Color(on ? 0xe8b54a : 0x000000);
      node.material.emissiveIntensity = on ? 0.25 : 0;
    }
  });
}
function applyHighlight() {
  parts.forEach((part, i) => setEmissive(part, i === selected || i === hovered));
}

// ---------- picking ----------
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
    const rect = stage.getBoundingClientRect();
    tooltip.style.display = "block";
    tooltip.style.left = (event.clientX - rect.left + 16) + "px";
    tooltip.style.top = (event.clientY - rect.top - 10) + "px";
    tooltip.textContent = parts[i].userData.name;
    stage.style.cursor = "pointer";
  } else { tooltip.style.display = "none"; stage.style.cursor = "grab"; }
});
// the show is automatic until the visitor takes the wheel
renderer.domElement.addEventListener("pointerdown",
  () => { controls.autoRotate = false; });

renderer.domElement.addEventListener("click", event => {
  const i = pick(event);
  if (i >= 0) select(i);
});

// ---------- explode / controls ----------
let explodeTarget = 0, explodeNow = 0;
explodeSlider.addEventListener("input", () => {
  explodeTarget = explodeSlider.value / 100;
});
document.getElementById("disassembleBtn")?.addEventListener("click", () => {
  explodeTarget = explodeTarget > 0.5 ? 0 : 1;
  explodeSlider.value = explodeTarget * 100;
  document.getElementById("viewer")?.scrollIntoView({ behavior: "smooth" });
});
document.getElementById("partsBtn").onclick = () =>
  document.getElementById("partsDrawer").classList.toggle("open");
document.getElementById("resetBtn").onclick = () => {
  explodeSlider.value = 0; explodeTarget = 0;
  camera.position.copy(HOME);
  controls.target.set(0, 0.05, 0);
  controls.autoRotate = true;
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
  explodeNow += (explodeTarget - explodeNow) * 0.07;
  for (const part of parts) {
    const { base, explode } = part.userData;
    part.position.set(base.x + explode.x * explodeNow,
                      base.y + explode.y * explodeNow,
                      base.z + explode.z * explodeNow);
  }
  screenMat.emissiveIntensity = 1.2 + Math.sin(Date.now() / 240) * 0.06; // CRT flicker
  controls.update();
  renderer.render(scene, camera);
});
