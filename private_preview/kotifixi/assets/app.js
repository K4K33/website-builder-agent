(() => {
  document.documentElement.classList.add('js');
  const menu = document.getElementById('menu-toggle');
  const panel = document.getElementById('mobile-menu');
  if (menu && panel) {
    const close = () => {menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Avaa valikko');panel.hidden=true;};
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Sulje valikko' : 'Avaa valikko');
      panel.hidden = !open;
    });
    panel.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
    document.addEventListener('keydown', e => { if(e.key === 'Escape') close(); });
    document.addEventListener('click', e => { if(!panel.hidden && !menu.contains(e.target) && !panel.contains(e.target)) close(); });
  }
  document.querySelectorAll('[data-year]').forEach(el => el.textContent=String(new Date().getFullYear()));
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduced) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if(entry.isIntersecting) { entry.target.classList.add('is-visible');observer.unobserve(entry.target); }
      });
    }, {threshold:.04,rootMargin:'0px 0px -30px 0px'});
    items.forEach(el => observer.observe(el));
  } else items.forEach(el => el.classList.add('is-visible'));
  const header=document.getElementById('header'), bar=document.getElementById('scroll-progress');
  let ticking=false;
  const update=() => {
    if(header) header.classList.toggle('is-sticky',window.scrollY>40);
    if(bar){const total=document.documentElement.scrollHeight-innerHeight;bar.style.width=(total>0?(scrollY/total*100):0)+'%';}
    ticking=false;
  };
  addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(update);ticking=true;}},{passive:true});update();
  const form=document.getElementById('contact-form');
  if(form) form.addEventListener('submit',e=>{
    e.preventDefault();
    if(!form.reportValidity()) return;
    const fd=new FormData(form);
    const name=String(fd.get('name')||'').trim(),email=String(fd.get('email')||'').trim();
    const service=String(fd.get('service')||'').trim(),message=String(fd.get('message')||'').trim();
    if(!name||!email||!service||!message) return;
    const sub=encodeURIComponent('Kotifixi – yhteydenotto: '+service);
    const body=encodeURIComponent('Hei Kotifixi!\n\nPalvelu: '+service+'\n\n'+message+'\n\nNimi: '+name+'\nSähköposti: '+email);
    const status=document.getElementById('form-feedback');
    if(status) status.textContent='Sähköpostisovellus avautuu. Lähetä viesti siellä, jos haluat.';
    window.location.href='mailto:kotifixi@gmail.com?subject='+sub+'&body='+body;
  });
})();