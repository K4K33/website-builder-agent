/* Woodtool concept — progressive, accessible interaction. No hidden ordering, no checkout or fake lead collection. */
(()=>{"use strict";
const menu=document.querySelector('[data-menu]'),nav=document.querySelector('.main-nav');
if(menu&&nav){
 const close=()=>{menu.setAttribute('aria-expanded','false');nav.classList.remove('open')};
 menu.addEventListener('click',()=>{const expanded=menu.getAttribute('aria-expanded')==='true';menu.setAttribute('aria-expanded',String(!expanded));nav.classList.toggle('open',!expanded)});
 nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
 document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
 document.addEventListener('click',e=>{if(!menu.contains(e.target)&&!nav.contains(e.target))close()});
}
document.documentElement.classList.add('js');
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
const reveal=document.querySelectorAll('[data-reveal]');
if(reduced.matches||!('IntersectionObserver' in window)){
 reveal.forEach(el=>el.classList.add('visible'));
}else{
 const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');io.unobserve(e.target)}}),{threshold:.06,rootMargin:'0px 0px -6% 0px'});
 reveal.forEach(el=>io.observe(el));
}
/* Real, noticeable material-light response; no scroll jank or fake 3D product. */
const panel=document.querySelector('[data-premium-interaction="pointer-depth"]');
if(panel&&!reduced.matches&&window.matchMedia('(pointer:fine)').matches){
 let inFlight=false,targetX=48,targetY=40;
 panel.addEventListener('pointermove',e=>{
  const r=panel.getBoundingClientRect();
  targetX=Math.max(0,Math.min(100,(e.clientX-r.left)/r.width*100));
  targetY=Math.max(0,Math.min(100,(e.clientY-r.top)/r.height*100));
  if(inFlight)return;
  inFlight=true;
  requestAnimationFrame(()=>{
   panel.style.setProperty('--px',targetX.toFixed(2)+'%');
   panel.style.setProperty('--py',targetY.toFixed(2)+'%');
   panel.style.setProperty('--shiftx',((50-targetX)*.11).toFixed(2)+'px');
   panel.style.setProperty('--shifty',((50-targetY)*.11).toFixed(2)+'px');
   inFlight=false;
  });
 },{passive:true});
}
const allFilters=[...document.querySelectorAll('[data-filter]')], works=[...document.querySelectorAll('[data-category]')];
function setFilter(value){
 allFilters.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.filter===value)));
 works.forEach(item=>item.hidden=value!=='all'&&item.dataset.category!==value);
}
allFilters.forEach(button=>button.addEventListener('click',()=>setFilter(button.dataset.filter)));
const dialog=document.querySelector('#work-dialog');
if(dialog&&typeof dialog.showModal==='function'){
 const photo=dialog.querySelector('img'),caption=dialog.querySelector('[data-dialog-caption]'),close=dialog.querySelector('[data-close-dialog]');
 const openButtons=[...document.querySelectorAll('[data-image-open]')];
 openButtons.forEach(button=>button.addEventListener('click',()=>{
   photo.src=button.dataset.imageOpen;
   const im=button.querySelector('img');photo.alt=im?im.alt:'';
   caption.textContent=button.dataset.title||'';
   dialog.showModal();close.focus();
 }));
 close?.addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()});
}
})();