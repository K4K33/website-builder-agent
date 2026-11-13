
'use strict';
(() => {
 const header=document.querySelector('.site-header');
 const toggle=document.querySelector('.mobile-toggle');
 const nav=document.querySelector('.main-nav');
 if(header&&toggle&&nav){
  const close=()=>{header.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');};
  toggle.addEventListener('click',()=>{let show=!header.classList.contains('menu-open');header.classList.toggle('menu-open',show);toggle.setAttribute('aria-expanded',String(show));});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
  document.addEventListener('click',e=>{if(!header.contains(e.target))close();});
  nav.addEventListener('click',e=>{if(e.target.closest('a'))close();});
 }
 const animateEls=[...document.querySelectorAll('.reveal')];
 if('IntersectionObserver' in window&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
  let obs=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add('visible');obs.unobserve(e.target);}}, {threshold:0.08,rootMargin:'0px 0px 60px 0px'});
  animateEls.forEach(el=>obs.observe(el));
 }else animateEls.forEach(el=>el.classList.add('visible'));
 const form=document.querySelector('#contact-form');
 if(form)form.addEventListener('submit',event=>{
  event.preventDefault();
  if(!form.reportValidity())return;
  const data=new FormData(form);
  const field=name=>String(data.get(name)||'').trim();
  const subject='Yhteydenotto Sähkö247:n verkkosivudemon kautta: '+field('topic');
  const message=['Nimi: '+field('name'),'Puhelin: '+field('phone'),'Sähköposti: '+field('email'),'Aihe: '+field('topic'),'','Viesti:',field('message'),'','Lähetetään sähköpostiohjelman kautta.'];
  const url='mailto:asiakaspalvelu@sahko247.fi?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(message.join('\n'));
  window.location.href=url;
  const note=document.querySelector('#form-feedback');
  if(note){note.hidden=false;note.textContent='Sähköpostiohjelma avautuu. Viesti lähetetään vasta, kun vahvistat sen siellä.';}
 });
})();
