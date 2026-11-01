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
  if(form){
    const startedAt=Date.now();
    let sending=false;
    const status=document.getElementById('form-status');
    const button=form.querySelector('button[type="submit"]');
    const endpoint='https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-kotifixi-demo-contact';
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      if(sending||!form.reportValidity())return;
      const fd=new FormData(form);
      const payload={
        name:String(fd.get('name')||'').trim(),
        email:String(fd.get('email')||'').trim(),
        service:String(fd.get('service')||'').trim(),
        message:String(fd.get('message')||'').trim(),
        website:String(fd.get('website')||''),
        test_consent:fd.get('test_consent')==='on',
        started_at:startedAt
      };
      if(!payload.test_consent)return;
      sending=true;
      if(button){button.disabled=true;button.textContent='Lähetetään…';}
      if(status){status.dataset.status='';status.textContent='Tallennetaan testiviestiä…';}
      try{
        const response=await fetch(endpoint,{
          method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify(payload),cache:'no-store'
        });
        const result=await response.json();
        if(!response.ok||result.ok!==true||!result.reference)
          throw new Error(result.error||'Tallennusta ei vahvistettu.');
        if(status){status.dataset.status='success';status.textContent='Testiviesti tallennettu onnistuneesti Kaurivon testiympäristöön. Tunnus: '+String(result.reference).slice(0,8)+'. Viestiä ei lähetetty Kotifixille.';}
        form.reset();
        if(button)button.textContent='Testiviesti tallennettu';
      }catch(error){
        if(status){status.dataset.status='error';status.textContent='Lähetys epäonnistui: '+String(error.message||'Yritä uudelleen.');}
        if(button)button.textContent='Lähetä testiviesti';
      }finally{
        sending=false;
        if(button)button.disabled=false;
      }
    });
  }
})();