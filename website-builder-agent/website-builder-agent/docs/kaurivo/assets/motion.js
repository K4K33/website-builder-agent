(() => {
  "use strict";
  const root = document.documentElement;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Static sites mark their script with data-auto: the same rules as annotate()
  // run here, so the HTML (and its SEO markup) never has to be rewritten.
  const me = document.currentScript;
  if (me && me.hasAttribute('data-auto')) {
    const skip = el => el.closest('header,nav,footer,form,[data-story],[data-hero-copy],[data-no-motion],[data-reveal]');
    const main = document.querySelector('main') || document.body;
    const sections = [...main.querySelectorAll('section')].filter(s => !s.parentElement.closest('section'));
    for (const section of sections.slice(1)) {
      if (section.hasAttribute('data-story') || section.hasAttribute('data-no-motion')) continue;
      for (const h of section.querySelectorAll('h2')) if (!skip(h)) h.dataset.reveal = 'rise';
      for (const parent of section.querySelectorAll('*')) {
        if (skip(parent) || parent.closest('[data-reveal="stagger"]')) continue;
        const kids = [...parent.children];
        if (kids.length < 3) continue;
        const keys = kids.map(k => [...k.classList].sort().join(' ') || k.tagName);
        const counts = {}; keys.forEach(k => counts[k] = (counts[k] || 0) + 1);
        const common = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
        if (counts[common] < 3 || counts[common] < kids.length * .6) continue;
        parent.dataset.reveal = 'stagger';
        kids.filter((k, i) => keys[i] === common).forEach((k, i) => {
          k.setAttribute('data-si', ''); k.style.setProperty('--i', i);
          if (k.querySelector('img,picture,video') && (k.tagName === 'A' || k.querySelector('a'))) k.classList.add('mo-card');
        });
      }
      for (const m of section.querySelectorAll('img,picture,video')) {
        if (skip(m) || m.closest('[data-depth-wall]') || (m.width && m.width < 280)) continue;
        let frame = ['FIGURE', 'PICTURE', 'DIV'].includes(m.parentElement.tagName) ? m.parentElement : m;
        if (frame.tagName === 'PICTURE') frame = frame.parentElement;
        if (!frame.hasAttribute('data-reveal')) frame.dataset.reveal = 'media';
      }
    }
  }
  root.classList.add('mo-js');
  const ease = t => 1 - Math.pow(1 - t, 3);
  const items = [...document.querySelectorAll('[data-reveal],[data-depth-wall]')].map(el => ({el, cur: -1, wall: el.hasAttribute('data-depth-wall')}));
  const tones = [...document.querySelectorAll('[data-tone]')];
  let toneCur = null, running = false;
  const target = it => {
    const r = it.el.getBoundingClientRect(), vh = innerHeight;
    if (it.wall) return Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
    return ease(Math.min(1, Math.max(0, (vh - r.top) / (vh * .6))));
  };
  const hex = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  function toneTarget() {
    let best = null, bestDist = 1e9;
    const mid = innerHeight * .55;
    for (const s of tones) {
      const r = s.getBoundingClientRect();
      const d = r.top <= mid && r.bottom >= mid ? 0 : Math.min(Math.abs(r.top - mid), Math.abs(r.bottom - mid));
      if (d < bestDist) { bestDist = d; best = s; }
    }
    return best && /^#[0-9a-f]{6}$/i.test(best.dataset.tone) ? hex(best.dataset.tone) : null;
  }
  function frame() {
    let moving = false;
    for (const it of items) {
      const t = target(it);
      const next = it.cur < 0 ? t : it.cur + (t - it.cur) * .16;
      if (Math.abs(next - t) > .0008) moving = true;
      const v = Math.abs(next - t) > .0008 ? next : t;
      if (Math.abs(v - it.cur) > .0004) {
        it.cur = v;
        it.el.style.setProperty(it.wall ? '--pass' : '--v', v.toFixed(4));
      }
    }
    if (tones.length) {
      const t = toneTarget();
      if (t) {
        toneCur = toneCur ? toneCur.map((c, i) => c + (t[i] - c) * .12) : t;
        if (toneCur.some((c, i) => Math.abs(c - t[i]) > .5)) moving = true;
        document.body.style.backgroundColor = `rgb(${toneCur.map(Math.round).join(',')})`;
      }
    }
    running = moving;
    if (moving) requestAnimationFrame(frame);
  }
  const kick = () => { if (!running) { running = true; requestAnimationFrame(frame); } };
  addEventListener('scroll', kick, {passive: true});
  addEventListener('resize', kick);
  frame();
})();
