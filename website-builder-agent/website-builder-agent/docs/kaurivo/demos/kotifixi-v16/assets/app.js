(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const menu = document.getElementById('menu-toggle');
  const nav = document.getElementById('mobile-menu');
  if (menu && nav) {
    const close = () => {
      nav.hidden = true;
      menu.setAttribute('aria-expanded', 'false');
      menu.setAttribute('aria-label', 'Avaa valikko');
    };
    menu.addEventListener('click', () => {
      const opening = menu.getAttribute('aria-expanded') !== 'true';
      nav.hidden = !opening;
      menu.setAttribute('aria-expanded', String(opening));
      menu.setAttribute('aria-label', opening ? 'Sulje valikko' : 'Avaa valikko');
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    document.addEventListener('click', e => {
      if (!nav.hidden && !nav.contains(e.target) && !menu.contains(e.target)) close();
    });
    const breakpoint = window.matchMedia('(min-width: 941px)');
    if (typeof breakpoint.addEventListener === 'function') breakpoint.addEventListener('change', e => { if (e.matches) close(); });
  }
  // Native wheel/touchpad/touch scrolling needs no scroll-position listener.
  document.querySelectorAll('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

  // V11: lightweight pointer-only 3D tilt. No scroll/resize listener, no WebGL.
  // Disabled on touch devices, reduced motion and non-hover environments.
  const heroArt = document.querySelector('.hero-visual-3d');
  if (heroArt && 'requestAnimationFrame' in window &&
      window.matchMedia('(hover: hover) and (pointer: fine)').matches &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const frame = heroArt.querySelector('.hero-photo-frame');
    if (frame) {
      let queued = false;
      let px = 0, py = 0;
      heroArt.addEventListener('pointermove', e => {
        px = e.clientX;
        py = e.clientY;
        if (queued) return;
        queued = true;
        window.requestAnimationFrame(() => {
          queued = false;
          const b = heroArt.getBoundingClientRect();
          const x = Math.max(-1, Math.min(1, (px - b.left) / b.width * 2 - 1));
          const y = Math.max(-1, Math.min(1, (py - b.top) / b.height * 2 - 1));
          frame.style.setProperty('--hero-tilt-x', (-y * 2.5).toFixed(2) + 'deg');
          frame.style.setProperty('--hero-tilt-y', (x * 3).toFixed(2) + 'deg');
        });
      }, { passive: true });
      heroArt.addEventListener('pointerleave', () => {
        frame.style.removeProperty('--hero-tilt-x');
        frame.style.removeProperty('--hero-tilt-y');
      });
    }
  }

  // Native scrolling remains entirely browser-owned. Reveal only sections
  // already outside the first viewport, with a one-shot IntersectionObserver.
  // If JS is disabled, unsupported or reduced motion is preferred, text
  // remains immediately visible.
  if ('IntersectionObserver' in window &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const targets = document.querySelectorAll(
      '.section-heading, .editorial-card, .approach-layout, .price-category, ' +
      '.tax-info, .service-row, .about-content-grid, .contact-layout'
    );
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px 20px 0px', threshold: 0.08 });
    targets.forEach(el => {
      // Never hide first-viewport or already-visible sections.
      if (el.getBoundingClientRect().top > window.innerHeight + 20) {
        el.classList.add('scroll-reveal');
        observer.observe(el);
      }
    });
  }


  // If an external example photo is unavailable, keep the editorial
  // layout and provide explicit text instead of showing a broken image.
  document.querySelectorAll('img').forEach(img => {
    const failed = () => {
      const frame = img.parentElement;
      if (frame) frame.classList.add('image-unavailable');
      img.style.opacity = '0';
      if (frame && !frame.querySelector('.image-fallback')) {
        const label = document.createElement('span');
        label.className = 'image-fallback';
        label.textContent = 'Esimerkkikuva ei ole saatavilla';
        frame.append(label);
      }
    };
    img.addEventListener('error', failed);
    if (img.complete && !img.naturalWidth) failed();
  });

  // Preserve the selected real service context from the home/service pages.
  // Only a closed allowlist can enter the test form; no script/HTML injection.
  const serviceParam = new URLSearchParams(window.location.search).get('palvelu');
  const serviceSelect = document.getElementById('cust-service');
  const allowedServices = new Set([
    'Pihatyöt', 'Kodin askareet', 'Pienet korjaukset', 'Renkaiden vaihto', 'Muu apu'
  ]);
  if (serviceSelect && allowedServices.has(serviceParam)) {
    serviceSelect.value = serviceParam;
  }

  // This demo form sends to the existing Kaurivo TEST endpoint, not Kotifixi.
  // Never claim this test submission was delivered to the actual business.
  const form = document.getElementById('contact-form');
  if (!form) return;
  const endpoint = 'https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-kotifixi-demo-contact';
  const startedAt = Date.now();
  const status = document.getElementById('form-status');
  const button = form.querySelector('button[type="submit"]');
  let sending = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || !form.reportValidity()) return;
    const fd = new FormData(form);
    const payload = {
      name: String(fd.get('name') || '').trim(),
      email: String(fd.get('email') || '').trim(),
      service: String(fd.get('service') || ''),
      message: String(fd.get('message') || '').trim(),
      website: String(fd.get('website') || ''),
      test_consent: fd.get('test_consent') === 'on',
      started_at: startedAt
    };
    if (!payload.test_consent) return;
    sending = true;
    button.disabled = true;
    button.textContent = 'Tallennetaan…';
    status.dataset.status = '';
    status.textContent = 'Tallennetaan testiviestiä…';
    try {
      const resultResponse = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), cache: 'no-store'
      });
      const result = await resultResponse.json();
      if (!resultResponse.ok || result.ok !== true || !result.reference) {
        throw new Error(result.error || 'Tallennusta ei voitu vahvistaa.');
      }
      status.dataset.status = 'success';
      status.textContent = 'Testiviesti tallennettu Kaurivon testiympäristöön. Tunnus: ' +
        String(result.reference).slice(0, 8) + '. Viestiä ei lähetetty Kotifixille.';
      form.reset();
      button.textContent = 'Lähetä uusi testiviesti';
    } catch (error) {
      status.dataset.status = 'error';
      status.textContent = 'Tallennus epäonnistui: ' + (error?.message || 'Yritä uudelleen.');
      button.textContent = 'Lähetä testiviesti';
    } finally {
      sending = false;
      button.disabled = false;
    }
  });
})();
