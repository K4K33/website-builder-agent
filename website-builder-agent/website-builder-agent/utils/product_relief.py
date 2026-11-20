"""Touchable 3D product: a free relief model made from the company's own photo.

The model marks a verified product photo with ``data-kaurivo-product``. The
builder cuts the product out (U2-Net-p mask) and estimates its shape (Depth
Anything V2), both locally and free. A small WebGL shader then renders the
product as a floating relief: it turns toward the pointer or finger and with
scroll, is lit from its own surface normals and casts a soft shadow.

The cut-out is accepted only when the product is clearly separated from its
background; otherwise, and for reduced motion or without WebGL, the authored
photo stays exactly as written.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from posixpath import normpath
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

PRODUCT_BRIEF = """
TOUCHABLE PRODUCT (optional, for a verified product or object the company
sells or makes, photographed on its own): write an ordinary figure and the
builder turns it into a touchable 3D product when the cut-out is clean:

<figure data-kaurivo-product>
  <img src="assets/product.webp" alt="Exact product name">
  <figcaption>Verified product name or fact</figcaption>
</figure>

Use at most two per page, only staged photos of a single product. Never use
it for people, interiors, buildings or busy scenes. Give the figure a good
static layout; it is what reduced-motion and no-WebGL visitors see.
""".strip()

MAX_PER_PAGE = 2
COVERAGE = (0.06, 0.75)
MAX_EDGE_SHARE = 0.18
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

_STYLE = """
[data-kaurivo-product]{position:relative}
[data-kaurivo-product] canvas[data-product-canvas]{position:absolute;pointer-events:none;opacity:0;transition:opacity .5s ease}
[data-kaurivo-product][data-product-active] canvas[data-product-canvas]{opacity:1}
[data-kaurivo-product][data-product-active] > img{visibility:hidden}
"""

SCRIPT = r"""
(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const VERT = 'attribute vec2 p;varying vec2 v;void main(){v=p*.5+.5;gl_Position=vec4(p,0.,1.);}';
  const FRAG = `precision highp float;varying vec2 v;uniform sampler2D im,dp,mk;uniform vec2 tilt,fit;
vec2 map(vec2 u){return (u-.5)*fit+.5;}
void main(){vec2 u=map(v);vec2 s=u;
 for(int k=0;k<6;k++){float d=texture2D(dp,s).r;s=u-tilt*(d-.45)*.16;}
 float inside=step(0.,s.x)*step(s.x,1.)*step(0.,s.y)*step(s.y,1.);
 float a=texture2D(mk,clamp(s,0.,1.)).r*inside;
 vec2 e=vec2(.004,0.);
 float dx=texture2D(dp,s+e.xy).r-texture2D(dp,s-e.xy).r,dy=texture2D(dp,s+e.yx).r-texture2D(dp,s-e.yx).r;
 vec3 n=normalize(vec3(-dx*9.,-dy*9.,1.));vec3 l=normalize(vec3(-.35+tilt.x,.55+tilt.y,.8));
 vec3 c=texture2D(im,clamp(s,0.,1.)).rgb*(.82+.32*max(dot(n,l),0.))+pow(max(dot(reflect(-l,n),vec3(0.,0.,1.)),0.),24.)*.18;
 float sh=0.;vec2 o=vec2(-tilt.x*.03,.045-tilt.y*.02);
 for(int k=0;k<4;k++){vec2 q=map(v)+o+vec2(float(k)-1.5,0.)*.012;sh+=texture2D(mk,clamp(q,0.,1.)).r*step(0.,q.y)*step(q.y,1.);}
 sh=sh*.25*.28;float outA=a+(1.-a)*sh;
 gl_FragColor=vec4(c*a,outA);}`;
  const load = src => new Promise((ok, fail) => { const i = new Image(); i.onload = () => ok(i); i.onerror = fail; i.src = src; });
  for (const figure of document.querySelectorAll('[data-kaurivo-product][data-product]')) {
    const cfg = JSON.parse(figure.getAttribute('data-product'));
    const photo = figure.querySelector(':scope > img');
    const canvas = figure.querySelector('canvas[data-product-canvas]');
    const gl = canvas.getContext('webgl', {premultipliedAlpha: true, alpha: true, antialias: true});
    if (!gl || !photo) continue;
    const sh = (t, c) => { const s = gl.createShader(t); gl.shaderSource(s, c); gl.compileShader(s); return s; };
    const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) continue; gl.useProgram(pr);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const at = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(at); gl.vertexAttribPointer(at, 2, gl.FLOAT, false, 0, 0);
    const U = n => gl.getUniformLocation(pr, n);
    ['im','dp','mk'].forEach((n, k) => gl.uniform1i(U(n), k));
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    const tex = (unit, image) => { const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
      for (const [k, val] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]])
        gl.texParameteri(gl.TEXTURE_2D, k, val); };
    const tilt = {x: 0, y: 0, tx: 0, ty: 0}; let visible = false, running = false, aspect = 1;
    function place() {
      const f = figure.getBoundingClientRect(), r = photo.getBoundingClientRect();
      Object.assign(canvas.style, {left: (r.left - f.left) + 'px', top: (r.top - f.top) + 'px', width: r.width + 'px', height: r.height + 'px'});
      const dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.round(r.width * dpr); canvas.height = Math.round(r.height * dpr); gl.viewport(0, 0, canvas.width, canvas.height);
      const box = r.width / Math.max(1, r.height), pad = 1.14;   // contain + room to turn
      gl.uniform2f(U('fit'), aspect > box ? pad : pad * box / aspect, aspect > box ? pad * aspect / box : pad);
    }
    function frame(time) {
      const r = figure.getBoundingClientRect();
      const scroll = Math.max(-1, Math.min(1, (r.top + r.height / 2 - innerHeight / 2) / innerHeight));
      tilt.x += (tilt.tx + Math.sin(time / 1900) * .08 - tilt.x) * .08;
      tilt.y += (tilt.ty + scroll * .35 - tilt.y) * .08;
      gl.uniform2f(U('tilt'), tilt.x, tilt.y);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      if (visible) requestAnimationFrame(frame); else running = false;
    }
    const aim = e => { const r = figure.getBoundingClientRect();
      tilt.tx = ((e.clientX - r.left) / r.width - .5) * 1.4; tilt.ty = (.5 - (e.clientY - r.top) / r.height) * 1.1; };
    Promise.all([load(cfg.img), load(cfg.depth), load(cfg.mask)]).then(([im, dp, mk]) => {
      aspect = im.naturalWidth / im.naturalHeight;
      tex(0, im); tex(1, dp); tex(2, mk); place();
      figure.setAttribute('data-product-active', '');
      addEventListener('resize', place, {passive: true});
      addEventListener('pointermove', aim, {passive: true});
      figure.addEventListener('pointerdown', aim, {passive: true});
      new IntersectionObserver(es => { visible = es[0].isIntersecting; if (visible && !running) { running = true; requestAnimationFrame(frame); } }).observe(figure);
    }).catch(() => {});
  }
})();
"""


def _staged(route: str, src: str, allowed: dict) -> str | None:
    try:
        parts = urlsplit(src or "")
    except ValueError:
        return None
    if parts.scheme or parts.netloc or parts.path.startswith("/") or parts.query or parts.fragment:
        return None
    resolved = normpath(str(PurePosixPath(route).parent / parts.path))
    return resolved if resolved in allowed else None


def clean_cutout(mask_path: Path) -> bool:
    """Accept a mask only for a clearly separated single product."""
    from PIL import Image
    from utils.depth_estimation import mask_coverage
    coverage = mask_coverage(mask_path)
    if not COVERAGE[0] <= coverage <= COVERAGE[1]:
        return False
    with Image.open(mask_path) as image:
        gray = image.convert("L")
        width, height = gray.size
        pixels = gray.load()
        border = [pixels[x, 0] for x in range(width)] + [pixels[x, height - 1] for x in range(width)]
        border += [pixels[0, y] for y in range(height)] + [pixels[width - 1, y] for y in range(height)]
        histogram = gray.histogram()
    edge_share = sum(1 for value in border if value > 128) / max(1, len(border))
    uncertain = sum(histogram[40:216]) / max(1, sum(histogram))
    return edge_share <= MAX_EDGE_SHARE and uncertain <= 0.12


def enhance_product_relief(html: str, *, route: str, media: list[dict],
                           site_root: str | Path | None) -> str:
    if "data-kaurivo-product" not in html or site_root is None:
        return html
    from utils import depth_estimation
    site_root = Path(site_root)
    soup = BeautifulSoup(html, "html.parser")
    allowed = {item["src"]: item["sha256"] for item in media
               if PurePosixPath(item["src"]).suffix.lower() in _IMAGE_EXT}
    prefix = "../" * (len(PurePosixPath(route).parts) - 1)
    count = 0
    for figure in soup.select("[data-kaurivo-product]"):
        for attr in ("data-product", "data-product-active"):
            figure.attrs.pop(attr, None)
        for old in figure.select("canvas[data-product-canvas]"):
            old.decompose()
        photo = figure.find("img", recursive=False)
        if (count >= MAX_PER_PAGE or figure.find_parent("main") is None or photo is None
                or not photo.get("alt", "").strip() or depth_estimation.disabled()):
            continue
        src = _staged(route, photo.get("src"), allowed)
        if not src or not (site_root / src).is_file():
            continue
        key = sha256((allowed[src] + "product-v1").encode()).hexdigest()[:12]
        folder = PurePosixPath("assets/product") / key
        mask, depth = site_root / folder / "mask.webp", site_root / folder / "depth.webp"
        if not mask.is_file() and depth_estimation.estimate_mask(site_root / src, mask) is None:
            continue
        if not clean_cutout(mask):
            continue
        if not depth.is_file() and depth_estimation.estimate_depth(site_root / src, depth) is None:
            continue
        figure["data-product"] = json.dumps({
            "img": prefix + src, "depth": prefix + str(folder / "depth.webp"),
            "mask": prefix + str(folder / "mask.webp")}, separators=(",", ":"))
        photo.insert_after(soup.new_tag("canvas", attrs={"data-product-canvas": "", "aria-hidden": "true"}))
        count += 1

    for item in soup.select("style[data-kaurivo-product-runtime], script[data-kaurivo-product-runtime]"):
        item.decompose()
    if count and soup.head and soup.body:
        for name, code, parent in (("style", _STYLE, soup.head), ("script", SCRIPT, soup.body)):
            tag = soup.new_tag(name, attrs={"data-kaurivo-product-runtime": ""})
            tag.string = code
            parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup))
