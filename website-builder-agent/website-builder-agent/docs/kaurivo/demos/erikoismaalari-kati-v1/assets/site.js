/* Purposeful progressive motion: original artwork remains readable without JS. */
(() => {
  const menu = document.querySelector('[data-menu]');
  const nav = document.querySelector('.nav');
  if (menu && nav) {
    const close = () => { menu.setAttribute('aria-expanded','false'); nav.classList.remove('open'); };
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click',close));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    document.addEventListener('click', e => { if (!nav.contains(e.target) && !menu.contains(e.target)) close(); });
  }
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const reveal = document.querySelectorAll('[data-reveal]');
  if (reducedMotion.matches || !('IntersectionObserver' in window)) {
    reveal.forEach(el => el.classList.add('visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => { if (entry.isIntersecting) {
        entry.target.classList.add('visible'); observer.unobserve(entry.target);
      } });
    }, { rootMargin:'0px 0px -5% 0px', threshold:.05 });
    reveal.forEach(el => observer.observe(el));
  }
  /* Optical highlight over the real painted mural. Motion disabled for touch
     and reduce-motion users. No continuous frame loops / scroll listeners. */
  const hero = document.querySelector('.hero');
  const pointerAllowed = window.matchMedia('(pointer:fine)');
  if (hero && !reducedMotion.matches && pointerAllowed.matches) {
    let scheduled = false, x=68, y=36;
    hero.addEventListener('pointermove',event => {
      const rect=hero.getBoundingClientRect();
      x=Math.min(100,Math.max(0,(event.clientX-rect.left)/rect.width*100));
      y=Math.min(100,Math.max(0,(event.clientY-rect.top)/rect.height*100));
      if(scheduled) return;
      scheduled=true;
      requestAnimationFrame(() => {
        hero.style.setProperty('--mx',x.toFixed(1)+'%');
        hero.style.setProperty('--my',y.toFixed(1)+'%');
        scheduled=false;
      });
    },{passive:true});
  }
  const dialog=document.querySelector('#lightbox');
  if(dialog && typeof dialog.showModal === 'function'){
    const image=dialog.querySelector('img');
    const caption=dialog.querySelector('[data-caption]');
    document.querySelectorAll('[data-open-image]').forEach(button=>{
      button.addEventListener('click',()=>{
        image.src=button.dataset.openImage;
        image.alt=button.querySelector('img')?.alt || 'Työnäytekuva';
        caption.textContent=button.dataset.caption || 'Alkuperäisen sivuston työkuva';
        dialog.showModal();
      });
    });
    dialog.querySelector('[data-close]')?.addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
  }
})();
