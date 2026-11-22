"""WebGL runtime for the depth scene: a 3D camera move through real photos.

Each layer is a staged company photo plus its depth map. Scroll drives a dolly
into the scene (near pixels move more than far ones) and a depth-ordered
dissolve to the next photo; pointer or touch tilts the camera and lifts a lens
where the visitor touches. Plain WebGL 1, no libraries. Without WebGL, with
reduced motion or before the first photo decodes, the authored poster stays.
"""

SCRIPT = r"""
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches) return;
  const VERT = 'attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;gl_Position=vec4(p,0.,1.);}';
  const FRAG = `precision highp float;varying vec2 v;
uniform sampler2D i0,d0,i1,d1,e0,m1;uniform vec2 c0,c1,cam;uniform vec3 touch;uniform float mixv,dolly0,dolly1,bp,reveal,draw,warp,style;
float h21(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y);}
// How the next build stage appears: 0 depth order, 1 coat (roller strokes), 2 tiles (row by row),
// 3 rise (bottom up). Returns reveal 0..1 and a shade for tiles being set.
vec2 stageReveal(float st,float t,vec2 u,float dn){
 if(st<.5)return vec2(smoothstep(1.-t*1.25,1.25-t*1.25,dn),0.);
 if(st<1.5){float n=9.;float b=floor(u.x*n);float edge=vn(vec2(u.x*40.,u.y*6.))*.06;
  float q=t*(n+1.2)-b-(1.-u.y)*1.1+edge;return vec2(smoothstep(0.,.06,q),0.);}
 if(st<2.5){float rows=12.;float r=floor(u.y*rows);
  // Tiles are laid row by row from the floor up, each row left to right.
  float q=t*(rows+1.3)-r-u.x*1.1;float l=smoothstep(0.,.07,q);
  return vec2(l,smoothstep(.07,0.,abs(q-.035))*.8);}
 float key=u.y+(vn(vec2(u.x*12.,u.y*3.))-.5)*.05;return vec2(smoothstep(key-.025,key+.025,t*1.08),0.);}
vec2 cover(vec2 u,vec2 c){return (u-.5)*c+.5;}
vec2 par(sampler2D dep,vec2 u,vec2 t,float dolly){
 vec2 z=(u-.5)/(1.+dolly*.5*(1.-warp))+.5;vec2 s=z;
 for(int k=0;k<6;k++){float d=texture2D(dep,s).r;
  vec2 disp=cam*(d-.35)+(s-.5)*d*dolly;vec2 tv=s-t;float f=exp(-dot(tv,tv)*22.);
  disp+=tv*f*touch.z*(.4+d);s=z-disp*warp;}
 return clamp(s,0.,1.);}
void main(){
 vec2 u0=cover(v,c0),u1=cover(v,c1);
 vec2 s0=par(d0,u0,cover(touch.xy,c0),dolly0);
 vec3 col=texture2D(i0,s0).rgb;
 if(bp>0.){float dn0=texture2D(d0,s0).r;float ln=texture2D(e0,s0).r*smoothstep(dn0-.15,dn0,draw*1.2);
  vec3 sketch=mix(vec3(.06,.12,.23),vec3(.86,.91,.98),ln);
  float above=smoothstep(reveal-.12,reveal,v.y*.75+(1.-dn0)*.25);
  col=mix(col,sketch,above*bp);}
 if(mixv>0.){vec2 s1=par(d1,u1,cover(touch.xy,c1),dolly1);
  float dn=texture2D(d1,s1).r;vec2 r=stageReveal(style,mixv,s1,dn);
  // Where the photos really change the work animates; elsewhere a quiet early crossfade.
  float ch=style<.5?1.:texture2D(m1,s1).r;float m=mix(smoothstep(0.,.4,mixv),r.x,ch);
  vec3 nx=texture2D(i1,s1).rgb*(1.-.22*r.y*ch);
  col=mix(col,nx,m);}
 vec2 q=v-.5;col*=1.-(.08+.2*warp)*dot(q,q);
 gl_FragColor=vec4(col,1.);}`;
  const load = src => new Promise((ok, fail) => {
    const image = new Image(); image.decoding = 'async'; image.onload = () => ok(image);
    image.onerror = fail; image.src = src;
  });
  for (const scene of document.querySelectorAll('[data-kaurivo-scrub="ready"][data-scrub-mode="depth"]')) {
    const cfg = JSON.parse(scene.getAttribute('data-depth'));
    const stage = scene.querySelector('[data-scrub-stage]');
    const canvas = scene.querySelector('canvas[data-scrub-canvas]');
    const bar = scene.querySelector('[data-scrub-progress]');
    const gl = canvas.getContext('webgl', {antialias: false, alpha: false});
    if (!gl) continue;
    const shader = (type, code) => { const s = gl.createShader(type); gl.shaderSource(s, code); gl.compileShader(s); return s; };
    const program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, VERT));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) continue;
    gl.useProgram(program);
    const buffer = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
    const at = gl.getAttribLocation(program, 'p'); gl.enableVertexAttribArray(at);
    gl.vertexAttribPointer(at, 2, gl.FLOAT, false, 0, 0);
    const U = name => gl.getUniformLocation(program, name);
    ['i0','d0','i1','d1','e0','m1'].forEach((n, k) => gl.uniform1i(U(n), k));
    const STYLE = {depth: 0, coat: 1, tiles: 2, rise: 3};
    gl.uniform1f(U('warp'), cfg.warp === 0 ? 0 : 1);
    const sketch = !!cfg.layers[0].lines;
    let sketchTex = null, drawStart = 0;
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    const texture = image => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
      for (const [k, val] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR],
                              [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]])
        gl.texParameteri(gl.TEXTURE_2D, k, val);
      return t;
    };
    const layers = cfg.layers.map(() => null);
    let white = null;
    const fetchLayer = k => Promise.all([load(cfg.layers[k].img), load(cfg.layers[k].depth),
                                          k === 0 && sketch ? load(cfg.layers[0].lines) : null,
                                          cfg.layers[k].mask ? load(cfg.layers[k].mask) : null])
      .then(([img, dep, lines, mask]) => {
        layers[k] = {img: texture(img), dep: texture(dep), aspect: img.naturalWidth / img.naturalHeight,
                     mask: mask ? texture(mask) : null, style: STYLE[cfg.layers[k].enter] || 0};
        if (lines) { sketchTex = texture(lines); drawStart = performance.now(); }
      });
    const chapters = [...scene.querySelectorAll('[data-kaurivo-scrub-copy] [data-at]')]
      .map(el => ({el, at: Math.min(.95, Math.max(0, parseFloat(el.dataset.at) || 0))})).sort((a, b) => a.at - b.at);
    let target = 0, progress = 0, visible = true, running = false;
    const pointer = {x: 0, y: 0, tx: 0, ty: 0, s: 0, ts: 0, ux: .5, uy: .5};
    const coverOf = aspect => {
      const a = canvas.width / Math.max(1, canvas.height);
      return aspect > a ? [a / aspect, 1] : [1, aspect / a];
    };
    function size() {
      const dpr = Math.min(devicePixelRatio || 1, 1.75);
      canvas.width = Math.round(stage.clientWidth * dpr); canvas.height = Math.round(stage.clientHeight * dpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    function bind(unit, tex) { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); }
    function draw(time) {
      progress += (target - progress) * .12;
      pointer.x += (pointer.tx - pointer.x) * .08; pointer.y += (pointer.ty - pointer.y) * .08;
      pointer.s += (pointer.ts - pointer.s) * .1;
      const n = cfg.layers.length, pos = Math.min(n - 1e-4, progress * n);
      const seg = Math.floor(pos), local = pos - seg;
      const a = layers[seg] || layers[0];
      const next = seg + 1 < n ? layers[seg + 1] : null;
      // A process transition (coat, tiles, rise) takes most of its segment so the
      // work is seen happening; a plain depth dissolve stays short.
      const processStyle = next && next.style ? next.style : 0;
      const mixv = next ? Math.max(0, Math.min(1, processStyle ? (local - .12) / .8 : (local - .68) / .32)) : 0;
      // No idle motion: the scene moves only when the visitor scrolls or points.
      const idle = 0;
      const orbit = (local - .5) * .05 * (seg % 2 ? -1 : 1);
      gl.uniform2f(U('cam'), orbit + pointer.x * .035 + idle, pointer.y * .025 + idle * .5);
      gl.uniform3f(U('touch'), pointer.ux, pointer.uy, pointer.s);
      // One continuous camera move over the whole sequence (no zoom jump per stage).
      const dolly = cfg.warp === 0 ? .04 + .22 * progress : .05 + .22 * local;
      gl.uniform1f(U('dolly0'), dolly);
      gl.uniform1f(U('dolly1'), cfg.warp === 0 ? dolly : .05 + .22 * Math.max(0, local - 1));
      gl.uniform1f(U('style'), processStyle);
      gl.uniform1f(U('mixv'), mixv);
      const building = sketchTex && seg === 0;
      gl.uniform1f(U('bp'), building ? 1 : 0);
      gl.uniform1f(U('draw'), Math.min(1, (time - drawStart) / 1800));
      gl.uniform1f(U('reveal'), Math.min(1.15, Math.max(0, local - .08) / .5 * 1.15));
      if (building) bind(4, sketchTex);
      gl.uniform2f(U('c0'), ...coverOf(a.aspect));
      bind(0, a.img); bind(1, a.dep);
      if (next) {
        gl.uniform2f(U('c1'), ...coverOf(next.aspect)); bind(2, next.img); bind(3, next.dep);
        if (!white) { white = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, white);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([255, 255, 255])); }
        bind(5, next.mask || white);
      }
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      scene.setAttribute('data-scrub-drawn', '');
      if (visible) requestAnimationFrame(draw); else running = false;
    }
    function start() { if (!running) { running = true; requestAnimationFrame(draw); } }
    function update() {
      const r = scene.getBoundingClientRect();
      target = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
      if (bar) bar.style.setProperty('--scrub-p', target.toFixed(4));
      let on = 0; chapters.forEach((c, k) => { if (target >= c.at) on = k; });
      chapters.forEach((c, k) => c.el.classList.toggle('is-on', k === on));
    }
    function aim(event, strength) {
      const r = stage.getBoundingClientRect();
      const x = (event.clientX - r.left) / r.width, y = (event.clientY - r.top) / r.height;
      pointer.tx = (x - .5) * 2; pointer.ty = (.5 - y) * 2; pointer.ux = x; pointer.uy = 1 - y; pointer.ts = strength;
    }
    fetchLayer(0).then(() => {
      scene.style.setProperty('--scrub-length', cfg.length);
      scene.setAttribute('data-scrub-active', '');
      size(); update(); start();
      addEventListener('scroll', update, {passive: true});
      addEventListener('resize', size, {passive: true});
      reduce.addEventListener('change', () => location.reload());
      stage.addEventListener('pointermove', e => aim(e, e.pointerType === 'mouse' ? .16 : .3), {passive: true});
      stage.addEventListener('pointerdown', e => aim(e, .32), {passive: true});
      for (const type of ['pointerleave', 'pointerup', 'pointercancel'])
        stage.addEventListener(type, () => { pointer.tx = pointer.ty = 0; pointer.ts = 0; }, {passive: true});
      new IntersectionObserver(entries => { visible = entries[0].isIntersecting; if (visible) start(); }).observe(stage);
      let k = 1; const more = () => { if (k < cfg.layers.length) fetchLayer(k++).then(more, more); }; more();
    }).catch(() => {});  // keep the authored poster layout
  }
})();
"""
