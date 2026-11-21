// Kaurivo build scene: a cutaway bathroom that builds itself on scroll.
// Illustration of the work stages, not a company project. Three.js (MIT).
import * as THREE from './three/three.module.js';
import { RoomEnvironment } from './three/RoomEnvironment.js';

const W = 2.4, D = 1.9, H = 2.5, T = 0.12;          // room inner size and wall thickness (m)
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const span = (t, a, b) => clamp((t - a) / (b - a));
const easeOut = x => 1 - Math.pow(1 - x, 3);
const easeInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const mix = (a, b, x) => a + (b - a) * x;

export const STAGES = [
  { at: 0.00, key: 'runko' }, { at: 0.20, key: 'putket' }, { at: 0.36, key: 'eristys' },
  { at: 0.56, key: 'laatat' }, { at: 0.84, key: 'valmis' },
];

function noiseTexture(base, spread, size = 256, specks = 0) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d'); const img = g.createImageData(size, size);
  const [r, gg, b] = base;
  for (let i = 0; i < size * size; i++) {
    const n = (Math.random() - .5) * spread + (Math.sin(i * 0.013) + Math.sin(i / size * 0.07)) * spread * .15;
    img.data[i * 4] = r + n; img.data[i * 4 + 1] = gg + n; img.data[i * 4 + 2] = b + n; img.data[i * 4 + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  for (let k = 0; k < specks; k++) {
    g.fillStyle = `rgba(${Math.random() < .5 ? '40,40,40' : '230,230,230'},${Math.random() * .25})`;
    g.beginPath(); g.arc(Math.random() * size, Math.random() * size, Math.random() * 2.2, 0, 7); g.fill();
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  return tex;
}

function tileGeometry(w, h, depth) {
  const r = 0.004, s = new THREE.Shape();
  s.moveTo(-w / 2 + r, -h / 2); s.lineTo(w / 2 - r, -h / 2); s.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
  s.lineTo(w / 2, h / 2 - r); s.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); s.lineTo(-w / 2 + r, h / 2);
  s.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); s.lineTo(-w / 2, -h / 2 + r); s.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: .002, bevelSize: .002, bevelSegments: 2, curveSegments: 3 });
  g.translate(0, 0, -depth / 2); return g;
}

export function mountBathroom(canvas, { reduce = false, background = null, accent = '#e0784f' } = {}) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  if (background) scene.background = new THREE.Color(background);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = .55;

  const camera = new THREE.PerspectiveCamera(30, 1, .1, 60);
  const root = new THREE.Group(); scene.add(root);
  root.position.set(.25, 0, 0);

  // Light: soft key from front-right, cool fill, warm interior light that switches on at the end.
  scene.add(new THREE.HemisphereLight(0xdfe8f2, 0x1a1f26, .55));
  const key = new THREE.DirectionalLight(0xfff3e6, 2.2);
  key.position.set(2.5, 9, 4); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 6; key.shadow.bias = -0.0004;
  Object.assign(key.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: 1, far: 20 });
  scene.add(key);
  const warm = new THREE.PointLight(0xffc98a, 0, 6, 1.6); warm.position.set(0, H - .15, -.1); warm.castShadow = true;
  warm.shadow.mapSize.set(1024, 1024); root.add(warm);

  // Ground: only a contact shadow, the model floats on the page colour.
  // Soft contact shadow (radial gradient), no hard-edged ground.
  const sc = document.createElement('canvas'); sc.width = sc.height = 256;
  const sg = sc.getContext('2d'); const grad = sg.createRadialGradient(128, 128, 8, 128, 128, 128);
  grad.addColorStop(0, 'rgba(0,0,0,.55)'); grad.addColorStop(.55, 'rgba(0,0,0,.22)'); grad.addColorStop(1, 'rgba(0,0,0,0)');
  sg.fillStyle = grad; sg.fillRect(0, 0, 256, 256);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(W * 2.1, D * 2.3),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, depthWrite: false }));
  ground.rotation.x = -Math.PI / 2; ground.position.set(-T / 2, -T - .002, -T / 2); root.add(ground);

  const concreteTex = noiseTexture([132, 134, 136], 26, 256, 900); concreteTex.repeat.set(2, 2);
  const concrete = new THREE.MeshStandardMaterial({ map: concreteTex, roughness: .92, metalness: 0 });
  const cut = new THREE.MeshStandardMaterial({ color: 0x9a9da1, roughness: .95 });   // cut faces of the section
  const membrane = new THREE.MeshStandardMaterial({ color: 0x5f9fd3, roughness: .45, metalness: 0, transparent: true, opacity: 0 });
  const tape = new THREE.MeshStandardMaterial({ color: 0xf2f2ee, roughness: .7, transparent: true, opacity: 0 });
  const tileTex = noiseTexture([190, 186, 179], 9, 128, 60);
  const tileMat = new THREE.MeshStandardMaterial({ map: tileTex, roughness: .38, metalness: 0 });
  const floorTileMat = new THREE.MeshStandardMaterial({ map: tileTex, color: 0x55575a, roughness: .6 });
  const copper = new THREE.MeshStandardMaterial({ color: 0xc07a4a, roughness: .32, metalness: 1 });
  const black = new THREE.MeshStandardMaterial({ color: 0x15171a, roughness: .35, metalness: .6 });
  const ceramic = new THREE.MeshStandardMaterial({ color: 0xf6f6f3, roughness: .12, metalness: 0 });
  const glass = new THREE.MeshPhysicalMaterial({ color: 0xdfeff2, roughness: .05, metalness: 0, transparent: true, opacity: 0, transmission: 0 });
  const shadowed = m => { m.castShadow = m.receiveShadow = true; return m; };

  // --- 1. Structure: slab and two walls (cutaway), rising from the ground.
  const slab = shadowed(new THREE.Mesh(new THREE.BoxGeometry(W + T, T, D + T), [cut, cut, concrete, cut, cut, cut]));
  slab.position.set(-T / 2, -T / 2, -T / 2); root.add(slab);
  const backGeo = new THREE.BoxGeometry(W + T, H, T); backGeo.translate(0, H / 2, 0);
  const back = shadowed(new THREE.Mesh(backGeo, [cut, cut, cut, concrete, concrete, concrete]));
  back.position.set(-T / 2, 0, -D / 2 - T / 2); root.add(back);
  const leftGeo = new THREE.BoxGeometry(T, H, D); leftGeo.translate(0, H / 2, 0);
  const left = shadowed(new THREE.Mesh(leftGeo, [concrete, cut, cut, cut, cut, concrete]));
  left.position.set(-W / 2 - T / 2, 0, 0); root.add(left);

  // --- 2. Pipes drawn along the walls, a floor drain.
  const pipes = [];
  const pipe = (pts, r = .016) => {
    const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)), false, 'catmullrom', .02);
    const geo = new THREE.TubeGeometry(curve, 160, r, 12, false);
    const mesh = shadowed(new THREE.Mesh(geo, copper)); geo.setDrawRange(0, 0); root.add(mesh); pipes.push(mesh); return mesh;
  };
  const zb = -D / 2 + .03;
  pipe([[-W / 2 + .03, .05, .75], [-W / 2 + .03, .05, -.5], [-W / 2 + .03, .05, -D / 2 + .03], [-.95, .05, zb], [-.95, .9, zb], [-.95, 1.05, zb]]);
  pipe([[-W / 2 + .03, .12, .75], [-W / 2 + .03, .12, -D / 2 + .1], [-.55, .12, zb], [.35, .12, zb], [.55, .12, zb], [.55, .45, zb]], .02);
  const drain = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.7, .012, .09), black));
  drain.position.set(-.75, .004, -.55); drain.scale.set(1e-3, 1, 1); root.add(drain);

  // --- 3. Waterproofing: membranes painted on, corner tape first.
  const membraneBack = new THREE.Mesh(new THREE.PlaneGeometry(W, H).translate(W / 2, H / 2, 0), membrane);
  membraneBack.position.set(-W / 2, 0, -D / 2 + .004); membraneBack.receiveShadow = true; root.add(membraneBack);
  const membraneLeft = new THREE.Mesh(new THREE.PlaneGeometry(D, H).translate(D / 2, H / 2, 0), membrane);
  membraneLeft.rotation.y = Math.PI / 2; membraneLeft.position.set(-W / 2 + .004, 0, D / 2); membraneLeft.receiveShadow = true; root.add(membraneLeft);
  const membraneFloor = new THREE.Mesh(new THREE.PlaneGeometry(W, D).translate(W / 2, D / 2, 0), membrane);
  membraneFloor.rotation.x = -Math.PI / 2; membraneFloor.position.set(-W / 2, .004, D / 2); membraneFloor.receiveShadow = true; root.add(membraneFloor);
  [membraneBack, membraneLeft, membraneFloor].forEach(m => m.scale.set(1e-3, 1, 1));
  const tapes = [
    [[.07, H, .004], [-W / 2 + .035, H / 2, -D / 2 + .006]],
    [[W, .07, .004], [0, .035, -D / 2 + .006]],
    [[.004, .07, D], [-W / 2 + .006, .035, 0]],
  ].map(([s, p]) => { const m = new THREE.Mesh(new THREE.BoxGeometry(...s), tape); m.position.set(...p); root.add(m); return m; });

  // --- 4. Tiles: 60x30 on walls, 30x30 on the floor, placed row by row.
  const tiles = [];
  const addTiles = (geo, mat, items) => {
    const mesh = new THREE.InstancedMesh(geo, mat, items.length);
    mesh.castShadow = mesh.receiveShadow = true; mesh.frustumCulled = false; root.add(mesh);
    tiles.push({ mesh, items });
  };
  const wallTile = tileGeometry(.592, .292, .01), floorTile = tileGeometry(.292, .292, .01);
  const backItems = [], leftItems = [], floorItems = [];
  for (let r = 0; r < 8; r++) for (let c = 0; c < 4; c++)
    backItems.push({ pos: new THREE.Vector3(-W / 2 + .3 + c * .6, .15 + r * .3, -D / 2 + .012), rot: new THREE.Euler(0, 0, 0),
                     from: new THREE.Vector3(0, .05, .9), order: r + c * .12 });
  for (let r = 0; r < 8; r++) for (let c = 0; c < 3; c++) {
    const z = -D / 2 + .3 + c * .6; if (z + .3 > D / 2 + .001) continue;
    leftItems.push({ pos: new THREE.Vector3(-W / 2 + .012, .15 + r * .3, z), rot: new THREE.Euler(0, Math.PI / 2, 0),
                     from: new THREE.Vector3(.9, .05, 0), order: r + c * .12 + .4 });
  }
  for (let r = 0; r < 6; r++) for (let c = 0; c < 8; c++)
    floorItems.push({ pos: new THREE.Vector3(-W / 2 + .15 + c * .3, .012, -D / 2 + .15 + r * .3), rot: new THREE.Euler(-Math.PI / 2, 0, 0),
                      from: new THREE.Vector3(0, .7, 0), order: r * .5 + c * .06 - 1.2 });
  addTiles(floorTile, floorTileMat, floorItems);
  addTiles(wallTile, tileMat, backItems);
  addTiles(wallTile, tileMat, leftItems);
  const maxOrder = Math.max(...tiles.flatMap(t => t.items.map(i => i.order)));
  const minOrder = Math.min(...tiles.flatMap(t => t.items.map(i => i.order)));
  const tmpM = new THREE.Matrix4(), tmpQ = new THREE.Quaternion(), tmpP = new THREE.Vector3(), tmpS = new THREE.Vector3();
  const tiltQ = new THREE.Quaternion();

  // --- 5. Fixtures: wall-hung toilet, rain shower, glass wall, linear drain cover, towel rail, mirror light.
  const fixtures = new THREE.Group(); root.add(fixtures);
  const bowl = shadowed(new THREE.Mesh(new THREE.CapsuleGeometry(.17, .2, 8, 24), ceramic));
  bowl.rotation.x = Math.PI / 2; bowl.scale.set(1, 1, .75); bowl.position.set(.55, .42, -D / 2 + .3);
  const seat = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.18, .18, .025, 32), ceramic));
  seat.scale.set(1, 1, 1.45); seat.position.set(.55, .53, -D / 2 + .32);
  const plate = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.22, .15, .015), black)); plate.position.set(.55, 1.05, -D / 2 + .025);
  const toilet = new THREE.Group(); toilet.add(bowl, seat, plate); fixtures.add(toilet);
  const shower = new THREE.Group();
  const riser = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, 1.15, 16), black)); riser.position.set(-.95, 1.55, -D / 2 + .06);
  const arm = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.01, .01, .32, 12), black)); arm.rotation.x = Math.PI / 2; arm.position.set(-.95, 2.12, -D / 2 + .2);
  const head = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.13, .13, .018, 40), black)); head.position.set(-.95, 2.1, -D / 2 + .36);
  const mixer = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.2, .07, .06), black)); mixer.position.set(-.95, 1.05, -D / 2 + .05);
  shower.add(riser, arm, head, mixer); fixtures.add(shower);
  const pane = new THREE.Mesh(new THREE.BoxGeometry(.012, 2.0, 1.0), glass); pane.position.set(-.35, 1.0, -D / 2 + .5); fixtures.add(pane);
  const paneBar = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.016, .016, 1.0), black)); paneBar.position.set(-.35, 2.0, -D / 2 + .5); fixtures.add(paneBar);
  const drainCover = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.7, .006, .07), black)); drainCover.position.set(-.75, .022, -.55); fixtures.add(drainCover);
  const rail = new THREE.Group();
  for (let k = 0; k < 4; k++) { const b = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.009, .009, .5, 12), black)); b.rotation.z = Math.PI / 2; b.position.set(0, k * .12, 0); rail.add(b); }
  rail.rotation.y = Math.PI / 2; rail.position.set(-W / 2 + .05, 1.05, .45); fixtures.add(rail);
  const mirrorLight = new THREE.Mesh(new THREE.BoxGeometry(.9, .03, .03), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffd6a0, emissiveIntensity: 0 }));
  mirrorLight.position.set(.55, 1.85, -D / 2 + .03); fixtures.add(mirrorLight);
  // Floating vanity with a basin and a round mirror on the back wall, right of the toilet? No: left wall.
  const oak = new THREE.MeshStandardMaterial({ map: noiseTexture([150, 112, 78], 16, 128, 0), roughness: .55 });
  const vanity = new THREE.Group();
  const cab = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.46, .42, .8), oak)); cab.position.set(0, .62, 0);
  const top = shadowed(new THREE.Mesh(new THREE.BoxGeometry(.48, .03, .82), ceramic)); top.position.set(0, .845, 0);
  const basin = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.17, .13, .1, 40), ceramic)); basin.position.set(.02, .91, 0);
  const tap = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, .22, 12), black)); tap.position.set(-.18, .97, 0);
  const spout = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.01, .01, .12, 12), black)); spout.rotation.z = Math.PI / 2; spout.position.set(-.12, 1.07, 0);
  const mirror = shadowed(new THREE.Mesh(new THREE.CylinderGeometry(.32, .32, .02, 64),
    new THREE.MeshStandardMaterial({ color: 0xc9d4da, roughness: .04, metalness: 1 })));
  mirror.rotation.z = Math.PI / 2; mirror.position.set(-.21, 1.55, 0);
  vanity.add(cab, top, basin, tap, spout, mirror);
  vanity.position.set(-W / 2 + .25, 0, .35); fixtures.add(vanity);
  rail.position.set(-.35, 1.05, -D / 2 + .05); rail.rotation.y = 0;
  const fixtureParts = [
    { obj: vanity, from: new THREE.Vector3(.6, 0, 0), a: .88, b: .95 },
    { obj: toilet, from: new THREE.Vector3(0, 0, .5), a: .86, b: .93 },
    { obj: shower, from: new THREE.Vector3(0, .5, 0), a: .87, b: .94 },
    { obj: drainCover, from: new THREE.Vector3(0, .3, 0), a: .86, b: .9 },
    { obj: rail, from: new THREE.Vector3(.4, 0, 0), a: .9, b: .96 },
    { obj: paneBar, from: new THREE.Vector3(0, .6, 0), a: .9, b: .97 },
    { obj: mirrorLight, from: new THREE.Vector3(0, 0, .3), a: .9, b: .96 },
  ].map(f => ({ ...f, home: f.obj.position.clone() }));

  // --- Camera path: high three-quarter view down to eye level, slowly orbiting.
  const camFrom = new THREE.Spherical(7.6, THREE.MathUtils.degToRad(58), THREE.MathUtils.degToRad(38));
  const camTo = new THREE.Spherical(6.6, THREE.MathUtils.degToRad(74), THREE.MathUtils.degToRad(24));
  const look = new THREE.Vector3(), lookFrom = new THREE.Vector3(0, .9, 0), lookTo = new THREE.Vector3(-.15, 1.15, -.2);
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 };
  addEventListener('pointermove', e => { pointer.tx = e.clientX / innerWidth - .5; pointer.ty = e.clientY / innerHeight - .5; }, { passive: true });

  let progress = reduce ? 1 : 0, shown = -1;
  function apply(t) {
    // Structure rises.
    const rise = easeOut(span(t, .0, .14));
    slab.scale.set(1, Math.max(1e-3, easeOut(span(t, 0, .05))), 1);
    back.scale.y = Math.max(1e-3, rise); left.scale.y = Math.max(1e-3, easeOut(span(t, .03, .17)));
    // Pipes draw.
    pipes.forEach(m => { m.visible = t < .5; });
    drain.visible = t < .86;
    pipes.forEach((m, i) => m.geometry.setDrawRange(0, Math.floor(m.geometry.index.count * easeInOut(span(t, .2 + i * .04, .32 + i * .04)) / 6) * 6));
    drain.scale.x = Math.max(1e-3, easeOut(span(t, .3, .35)));
    // Membrane.
    const tp = span(t, .36, .4); tapes.forEach(m => { m.material.opacity = tp; });
    membrane.opacity = span(t, .38, .41);
    membraneFloor.scale.x = Math.max(1e-3, easeInOut(span(t, .38, .45)));
    membraneBack.scale.x = Math.max(1e-3, easeInOut(span(t, .42, .5)));
    membraneLeft.scale.x = Math.max(1e-3, easeInOut(span(t, .46, .54)));
    // Grouting turns the joints from membrane blue to grey.
    const grout = span(t, .8, .86);
    membrane.color.setRGB(mix(.37, .33, grout), mix(.62, .32, grout), mix(.83, .31, grout));
    tape.opacity = tp * (1 - grout);
    // Tiles.
    const tileT = span(t, .56, .82);
    for (const { mesh, items } of tiles) {
      items.forEach((it, i) => {
        const local = clamp((tileT * (maxOrder - minOrder + 2.2) - (it.order - minOrder)) / 1.2);
        const k = easeOut(local);
        tmpP.copy(it.from).multiplyScalar(1 - k).add(it.pos);
        tmpQ.setFromEuler(it.rot); tiltQ.setFromAxisAngle(new THREE.Vector3(1, .3, 0).normalize(), (1 - k) * .9); tmpQ.multiply(tiltQ);
        const s = local <= 0 ? 1e-4 : mix(.6, 1, k); tmpS.set(s, s, s);
        mesh.setMatrixAt(i, tmpM.compose(tmpP, tmpQ, tmpS));
      });
      mesh.instanceMatrix.needsUpdate = true;
    }
    // Fixtures.
    for (const f of fixtureParts) {
      const k = easeOut(span(t, f.a, f.b));
      f.obj.visible = k > 0;
      f.obj.position.copy(f.from).multiplyScalar(1 - k).add(f.home);
    }
    glass.opacity = .22 * easeOut(span(t, .9, .97)); pane.visible = glass.opacity > 0;
    const lit = easeInOut(span(t, .93, 1));
    warm.intensity = 4.5 * lit; mirrorLight.material.emissiveIntensity = 2.2 * lit;
    key.intensity = mix(2.2, 1.2, lit); scene.environmentIntensity = mix(.55, .32, lit);
    // Camera.
    const c = easeInOut(t);
    const s = new THREE.Spherical(mix(camFrom.radius, camTo.radius, c), mix(camFrom.phi, camTo.phi, c),
                                  mix(camFrom.theta, camTo.theta, c) + pointer.x * .08);
    camera.position.setFromSpherical(s); camera.position.y += pointer.y * -.15;
    look.lerpVectors(lookFrom, lookTo, c); camera.lookAt(look);
  }
  function size() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false); camera.aspect = w / Math.max(1, h);
    // Fit the whole model: widen the lens as the frame gets narrower than 16:10.
    camera.fov = Math.min(56, 30 * Math.max(1, 1.62 / camera.aspect) ** .8); camera.updateProjectionMatrix();
  }
  let target = progress, running = false;
  function frame() {
    progress += (target - progress) * .14;
    pointer.x += (pointer.tx - pointer.x) * .06; pointer.y += (pointer.ty - pointer.y) * .06;
    apply(progress); renderer.render(scene, camera);
    const settled = Math.abs(target - progress) < 1e-4 && Math.abs(pointer.tx - pointer.x) < 1e-3;
    if (!settled) requestAnimationFrame(frame); else running = false;
  }
  function kick() { if (!running) { running = true; requestAnimationFrame(frame); } }
  size(); apply(progress); renderer.render(scene, camera);
  addEventListener('resize', () => { size(); kick(); }, { passive: true });
  addEventListener('pointermove', kick, { passive: true });
  return {
    set(p) { target = clamp(p); kick(); },
    jump(p) { target = progress = clamp(p); apply(progress); renderer.render(scene, camera); },
  };
}
