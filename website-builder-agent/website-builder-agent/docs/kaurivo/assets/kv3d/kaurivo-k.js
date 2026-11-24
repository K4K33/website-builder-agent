// Kaurivo hero: the K as three bevelled brushed-steel plates, lit in real time.
// Scroll pulls the camera back while the plates lock together, a light sweeps
// across the metal, then the mark turns aside for the headline. The cursor
// moves a soft light over the surface. Three.js r187 (MIT, ../LICENSE-three.txt).
//
// Rebuild: place three.module.js, three.core.js and RoomEnvironment.js from the
// Three.js r187 release in ./three/ and run
//   esbuild kaurivo-k.js --bundle --format=esm --minify --target=es2020 \
//     --legal-comments=eof --outfile=../kv3d.min.js
import * as THREE from './three/three.module.js';

const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const span = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOut = x => 1 - Math.pow(1 - x, 3);
const mix = (a, b, x) => a + (b - a) * x;

// The three shards of the K, traced from kaurivo-mark.webp (457 x 330 px).
const SHARDS = [
  { pts: [[106, 27], [212, 27], [212, 106], [107, 214]],               from: [-2.3, 1.3, 1.4], rot: [0.5, 0.9, -0.5], at: [0.0, 0.32] },
  { pts: [[325, 25], [451, 26], [26, 314]],                            from: [0.15, -0.2, 2.2], rot: [0.0, -0.35, -0.18], at: [0.0, 0.42] },
  { pts: [[208, 222], [296, 170], [432, 319], [297, 319]],              from: [2.3, -1.5, 1.2], rot: [-0.6, -0.7, 0.4], at: [0.03, 0.36] },
];
const S = 1 / 100, CX = 238, CY = 170;            // svg px -> scene units, centred

function brushedRoughness() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 64;
  const g = c.getContext('2d');
  g.fillStyle = '#7a7a7a'; g.fillRect(0, 0, 512, 64);
  for (let i = 0; i < 900; i++) {                // fine horizontal brush strokes
    const y = Math.random() * 64, v = 90 + Math.random() * 80;
    g.fillStyle = `rgba(${v},${v},${v},${0.12 + Math.random() * 0.25})`;
    g.fillRect(Math.random() * 512, y, 40 + Math.random() * 300, 0.6 + Math.random());
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(0.35, 3.2);
  return t;
}

// A dark photo studio: long softbox strips and a cool rim panel. Metal only looks
// like metal when it has something bright and something dark to reflect.
function studio() {
  const env = new THREE.Scene();
  env.background = new THREE.Color(0x05070b);
  const box = (w, h, x, y, z, ry, rx, color, power) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(power), side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.rotation.set(rx, ry, 0); env.add(m);
  };
  box(14, 1.2, 0, 6, 2, 0, Math.PI / 2, 0xffffff, 3.2);      // top strip
  box(1.4, 9, -7, 0.5, 2, Math.PI / 2, 0, 0xffffff, 2.4);    // left vertical softbox
  box(1.0, 9, 7, 0.5, -1, -Math.PI / 2, 0, 0xffffff, 1.4);   // right strip
  box(10, 4, 0, 0, -8, 0, 0, 0x7fa8d9, 0.9);                 // cool back panel
  box(6, 0.6, 0, -3.5, 6, 0, -0.4, 0xffffff, 1.6);           // low front kicker
  // big graded softbox behind the camera: the faces of the K reflect a soft
  // diagonal fall-off from bright to dark instead of a flat mirror
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const g = c.getContext('2d'), grad = g.createLinearGradient(0, 0, 256, 256);
  grad.addColorStop(0, '#2a323c'); grad.addColorStop(0.34, '#59626e'); grad.addColorStop(0.47, '#ffffff');
  grad.addColorStop(0.53, '#e9eef4'); grad.addColorStop(0.66, '#3a434e'); grad.addColorStop(0.82, '#8a96a4');
  grad.addColorStop(0.88, '#252c35'); grad.addColorStop(1, '#06090d');
  g.fillStyle = grad; g.fillRect(0, 0, 256, 256);   // a bright band and a second soft band
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const front = new THREE.Mesh(new THREE.PlaneGeometry(18, 11), new THREE.MeshBasicMaterial({ map: tex, side: THREE.DoubleSide }));
  front.material.color.setScalar(1.6);
  front.position.set(1.5, 1.5, 9); front.rotation.y = Math.PI; env.add(front);
  return env;
}

function shardMesh(pts, material) {
  const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2((x - CX) * S, (CY - y) * S)));
  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: 0.22, bevelEnabled: true, bevelThickness: 0.035, bevelSize: 0.03, bevelSegments: 5, curveSegments: 1,
  });
  geo.computeBoundingBox();
  const c = new THREE.Vector3(); geo.boundingBox.getCenter(c);
  geo.translate(-c.x, -c.y, -c.z);                // rotate each plate about its own centre
  const mesh = new THREE.Mesh(geo, material);
  mesh.userData.home = c;
  return mesh;
}

export function mountKaurivoK(canvas, { section, reduce = false, onReady } = {}) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  } catch (e) { return null; }
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(studio(), 0.02).texture;
  scene.environmentIntensity = 1.0;

  const steel = new THREE.MeshPhysicalMaterial({
    color: 0xe6ebf0, metalness: 1, roughness: 0.3, roughnessMap: brushedRoughness(),
    clearcoat: 0.5, clearcoatRoughness: 0.12, envMapIntensity: 1.0,
  });
  const mark = new THREE.Group(); scene.add(mark);
  const plates = SHARDS.map(s => { const m = shardMesh(s.pts, steel); mark.add(m); return { ...s, mesh: m }; });

  const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(-3, 4, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0x7fa8d9, 3.2); rim.position.set(4, 1.5, -4); scene.add(rim);
  const sweep = new THREE.SpotLight(0xffffff, 0, 14, 0.22, 0.6, 1.2); scene.add(sweep, sweep.target);
  const touch = new THREE.PointLight(0xdbe8ff, 0, 6, 1.6); scene.add(touch);

  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 80);
  const pointer = { x: 0, y: 0, tx: 0, ty: 0, on: 0 };
  addEventListener('pointermove', e => {
    pointer.tx = (e.clientX / innerWidth) * 2 - 1; pointer.ty = -((e.clientY / innerHeight) * 2 - 1); pointer.on = 1;
  }, { passive: true });

  let w = 0, h = 0, wide = true;
  function resize() {
    const r = canvas.getBoundingClientRect();
    if (r.width === w && r.height === h) return;
    w = r.width; h = r.height; wide = w / h > 0.9;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }

  let p = reduce ? 1 : 0, shown = reduce ? 1 : -1, t0 = performance.now();
  function target() {
    if (reduce || !section) return 1;
    const r = section.getBoundingClientRect(), room = Math.max(1, r.height - innerHeight);
    return clamp(-r.top / room);
  }

  function pose(prog, time) {
    // plates fly in from close to the camera and lock together
    for (const pl of plates) {
      const k = ease(span(prog, pl.at[0], pl.at[1])), i = 1 - k;
      const home = pl.mesh.userData.home;
      pl.mesh.position.set(home.x + pl.from[0] * i, home.y + pl.from[1] * i, home.z + pl.from[2] * i);
      pl.mesh.rotation.set(pl.rot[0] * i, pl.rot[1] * i, pl.rot[2] * i);
    }
    // camera: macro on the blade -> whole mark -> the mark steps aside for the copy
    const pull = ease(span(prog, 0, 0.46)), aside = ease(span(prog, 0.6, 0.84));
    const dist = mix(5.6, 10.5, pull);
    const orbit = mix(0.62, 0.18, pull) + mix(0, -0.32, aside);
    camera.position.set(Math.sin(orbit) * dist, mix(0.55, 0.25, pull), Math.cos(orbit) * dist);
    const look = new THREE.Vector3(mix(0.55, 0, pull), mix(0.1, 0, pull), 0);
    // aside: the camera looks past the mark, so it moves right on wide screens, up on tall ones
    const shift = wide ? new THREE.Vector3(mix(0, -1.6, aside), 0, 0) : new THREE.Vector3(0, mix(0, -1.25, aside), 0);
    camera.lookAt(look.add(shift));
    camera.fov = mix(26, wide ? 30 : 38, pull); camera.updateProjectionMatrix();
    // idle breathing + cursor tilt once assembled
    const settle = span(prog, 0.5, 0.7);
    mark.rotation.y = (Math.sin(time * 0.00035) * 0.03 + pointer.x * 0.12) * settle;
    mark.rotation.x = (Math.cos(time * 0.0003) * 0.02 - pointer.y * 0.08) * settle;
    // one light sweep across the locked metal
    const s = span(prog, 0.4, 0.62);
    sweep.intensity = Math.sin(s * Math.PI) * 140;
    sweep.position.set(mix(-5, 5, s), 2.5, 4.5); sweep.target.position.set(mix(-1.5, 1.5, s), 0, 0);
    // the cursor light
    touch.intensity = mix(touch.intensity, pointer.on * 14 * settle, 0.08);
    touch.position.set(pointer.x * 2.6, pointer.y * 1.6, 1.6);
  }

  let raf = 0, ready = false;
  function frame(now) {
    raf = 0; resize();
    const goal = target();
    p = shown < 0 ? goal : p + (goal - p) * 0.14;            // smoothed scroll
    pointer.x += (pointer.tx - pointer.x) * 0.08; pointer.y += (pointer.ty - pointer.y) * 0.08;
    pose(p, now - t0);
    renderer.render(scene, camera);
    shown = p;
    if (!ready) { ready = true; onReady && onReady(); }
    const moving = Math.abs(goal - p) > 0.0005 || Math.abs(pointer.tx - pointer.x) > 0.002 || span(p, 0.5, 1) > 0;
    if (moving && !reduce) raf = requestAnimationFrame(frame);
  }
  const kick = () => { if (!raf) raf = requestAnimationFrame(frame); };
  addEventListener('scroll', kick, { passive: true });
  addEventListener('resize', kick);
  addEventListener('pointermove', kick, { passive: true });
  // stop rendering when the hero is off screen
  if ('IntersectionObserver' in window && section) {
    new IntersectionObserver(([e]) => { if (e.isIntersecting) kick(); else if (raf) { cancelAnimationFrame(raf); raf = 0; } })
      .observe(section);
  }
  kick();
  return { render: () => { resize(); pose(p, 0); renderer.render(scene, camera); }, setProgress: v => { p = shown = v; pose(v, 0); renderer.render(scene, camera); } };
}

// Boot: mount into the first [data-kv3d] hero; keep the poster if WebGL is unavailable.
const hero = document.querySelector('[data-kv3d]');
if (hero) {
  const canvas = hero.querySelector('canvas');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gl = (() => { try { return !!document.createElement('canvas').getContext('webgl2'); } catch (e) { return false; } })();
  if (canvas && gl) {
    const api = mountKaurivoK(canvas, { section: hero, reduce, onReady: () => hero.classList.add('is-3d') });
    if (api) window.__kaurivoK = api;   // used by the browser QA to film fixed progress points
  } else hero.classList.add('no-3d');
}
