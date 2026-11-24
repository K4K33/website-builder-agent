(() => {
  const heroes = [...document.querySelectorAll('[data-copy-after]')];
  if (!heroes.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function update() {
    let building = false;
    for (const h of heroes) {
      const r = h.getBoundingClientRect(), room = r.height - innerHeight;
      const at = Math.min(.95, Math.max(.1, +h.dataset.copyAfter || .8));
      // A hero without scroll room (no animation to finish) shows its copy at once.
      const done = reduce || room < innerHeight * .25 || -r.top / room >= at;
      h.classList.toggle('is-done', done);
      if (r.top < innerHeight && r.bottom > 0 && !done) building = true;
    }
    document.documentElement.classList.toggle('hero-building', building);
  }
  heroes.forEach(h => h.classList.add('is-js'));
  addEventListener('scroll', () => requestAnimationFrame(update), {passive: true});
  addEventListener('resize', update);
  update();
})();
(() => {
  "use strict";
  const stories = [...document.querySelectorAll('[data-story]')];
  if (!stories.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const setup = stories.map(story => {
    const items = [...story.querySelectorAll('[data-k]')].map(el => {
      const [a, b] = el.dataset.k.split(',').map(Number);
      return {el, a, b: Math.max(b, a + .001), last: -1};
    });
    let stages = [];
    try { stages = JSON.parse(story.dataset.stages || '[]'); } catch (e) { stages = []; }
    story.classList.add('is-js');
    return {story, items, stages, caption: story.querySelector('[data-story-caption]'), last: -1};
  });
  function frame() {
    for (const s of setup) {
      const r = s.story.getBoundingClientRect(), room = Math.max(1, r.height - innerHeight);
      const p = reduce ? 1 : Math.min(1, Math.max(0, -r.top / room));
      if (Math.abs(p - s.last) < .0004) continue;
      s.last = p;
      s.story.style.setProperty('--p', p.toFixed(4));
      for (const it of s.items) {
        const k = ease(Math.min(1, Math.max(0, (p - it.a) / (it.b - it.a))));
        if (Math.abs(k - it.last) > .0005) { it.last = k; it.el.style.setProperty('--k', k.toFixed(4)); }
      }
      if (s.caption && s.stages.length) {
        const en = document.documentElement.lang === 'en';
        let text = '';
        for (const st of s.stages) if (p >= st[0]) text = (en && st[2]) || st[1];
        if (s.caption.textContent !== text) s.caption.textContent = text;
      }
    }
  }
  let queued = false;
  const request = () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; frame(); }); } };
  addEventListener('scroll', request, {passive: true});
  addEventListener('resize', request);
  new MutationObserver(request).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  frame();
})();
