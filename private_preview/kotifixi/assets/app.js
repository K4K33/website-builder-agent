(() => {
  document.documentElement.classList.add('js');
  const menu = document.getElementById('menu-btn');
  const nav = document.getElementById('mobile-nav');
  if (menu && nav) {
    function close() {nav.hidden=true;menu.setAttribute('aria-expanded','false');menu.setAttribute('aria-label','Avaa valikko');}
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded',String(open));
      menu.setAttribute('aria-label', open?'Sulje valikko':'Avaa valikko');
      nav.hidden = !open;
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click',close));
    document.addEventListener('keydown', e => {if(e.key==='Escape')close();});
    document.addEventListener('click', e => {if(!nav.hidden && !nav.contains(e.target) && !menu.contains(e.target)) close();});
    matchMedia('(min-width: 931px)').addEventListener('change', e => {if(e.matches)close();});
  }
  const header=document.getElementById('site-header');
  let frame=false;
  window.addEventListener('scroll',()=>{if(!frame){frame=true;requestAnimationFrame(()=>{if(header)header.classList.toggle('scrolled',window.scrollY>10);frame=false;});}},{passive:true});
  document.querySelectorAll('[data-year]').forEach(n => n.textContent=String(new Date().getFullYear()));
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const nodes=document.querySelectorAll('.reveal');
  if(!reduced && 'IntersectionObserver' in window){
    const io=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target);}});},{threshold:0.05,rootMargin:'0px 0px 30px 0px'});
    nodes.forEach(n=>io.observe(n));
  } else nodes.forEach(n=>n.classList.add('is-visible'));
  document.querySelectorAll('img').forEach(img => {img.addEventListener('error',()=>img.classList.add('image-unavailable'));if(img.complete&&!img.naturalWidth)img.classList.add('image-unavailable');});
  const form=document.getElementById('contact-form');
  if(form)form.addEventListener('submit',e=>{
    e.preventDefault();
    if(!form.reportValidity())return;
    const data=new FormData(form);
    const name=String(data.get('name')||'').trim(),email=String(data.get('email')||'').trim(),service=String(data.get('service')||'').trim(),message=String(data.get('message')||'').trim();
    if(!name||!email||!service||!message)return;
    const subject=encodeURIComponent('Kotifixi – yhteydenotto: '+service);
    const body=encodeURIComponent('Hei Kotifixi!\n\nPalvelu: '+service+'\n\n'+message+'\n\nNimi: '+name+'\nSähköposti: '+email);
    const status=document.getElementById('form-status');
    if(status)status.textContent='Sähköpostisovellus avautuu. Varmista lähettäminen itse.';
    window.location.href='mailto:kotifixi@gmail.com?subject='+subject+'&body='+body;
  });
})();