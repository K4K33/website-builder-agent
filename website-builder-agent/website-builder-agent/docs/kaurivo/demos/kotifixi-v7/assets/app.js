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
  const header = document.getElementById('site-header');
  let scrollFrame = false;
  window.addEventListener('scroll', () => {
    if (scrollFrame) return;
    scrollFrame = true;
    requestAnimationFrame(() => {
      header?.classList.toggle('scrolled', window.scrollY > 7);
      scrollFrame = false;
    });
  }, { passive: true });
  document.querySelectorAll('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

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
