
(()=>{'use strict';
const header=document.querySelector('.site-header');
const toggle=document.querySelector('.nav-toggle');
if(toggle&&header){
 toggle.addEventListener('click',()=>{
   const open=header.classList.toggle('menu-open');
   toggle.setAttribute('aria-expanded',String(open));
   toggle.setAttribute('aria-label',open?'Close menu':'Open menu');
 });
 document.querySelectorAll('.nav-links a').forEach(a=>a.addEventListener('click',()=>{
   header.classList.remove('menu-open');toggle.setAttribute('aria-expanded','false');
 }));
}
const year=document.querySelector('[data-year]');if(year)year.textContent=String(new Date().getFullYear());
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const reveal=document.querySelectorAll('.motion-in,.motion-underline');
if('IntersectionObserver' in window&&!reduced.matches){
 const ob=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){e.target.classList.add('show');ob.unobserve(e.target)}},{threshold:.07,rootMargin:'0px 0px -12px 0px'});
 reveal.forEach(el=>ob.observe(el));
}else{reveal.forEach(el=>el.classList.add('show'))}
const scene=document.querySelector('.hero-scene'),visual=document.querySelector('.hero-visual');
if(scene&&visual&&!reduced.matches&&matchMedia('(hover:hover) and (pointer:fine)').matches){
 let frame=0,x=0,y=0;
 scene.addEventListener('pointermove',e=>{
   const r=scene.getBoundingClientRect();
   x=((e.clientX-r.left)/r.width-.5)*9;
   y=-((e.clientY-r.top)/r.height-.5)*7;
   if(!frame)frame=requestAnimationFrame(()=>{
     visual.style.setProperty('--ry',x.toFixed(2)+'deg');
     visual.style.setProperty('--rx',y.toFixed(2)+'deg');
     frame=0;
   });
 },{passive:true});
 scene.addEventListener('pointerleave',()=>{
   if(frame)cancelAnimationFrame(frame);frame=0;
   visual.style.setProperty('--rx','0deg');visual.style.setProperty('--ry','0deg');
 });
}
const stage=document.querySelector('.process-stage'),steps=document.querySelectorAll('.timeline-item');
if(stage&&steps.length&&'IntersectionObserver' in window){
 const stepObserver=new IntersectionObserver(entries=>{
   for(const e of entries)if(e.isIntersecting){
      steps.forEach(s=>s.classList.remove('active'));
      e.target.classList.add('active');
      const n=e.target.getAttribute('data-step');
      stage.setAttribute('data-active',n);
      const cap=stage.querySelector('.stage-caption');
      if(cap)cap.textContent=String(n).padStart(2,'0')+' / 04  —  '+e.target.getAttribute('data-label');
   }
 },{threshold:.55});
 steps.forEach(s=>stepObserver.observe(s));
}else if(steps.length){steps[0].classList.add('active')}
const faqs=document.querySelectorAll('.faq-list details');
faqs.forEach(detail=>detail.addEventListener('toggle',()=>{if(detail.open){faqs.forEach(other=>{if(other!==detail)other.open=false})}}));
const form=document.getElementById('enquiry-form');
if(form)form.addEventListener('submit',e=>{
 e.preventDefault();if(!form.reportValidity())return;
 const val=name=>(form.elements.namedItem(name)?.value||'').trim();
 const data=[['Name',val('name')],['Email',val('email')],['Company',val('company')],['Website',val('website')||'Not provided'],['Project',val('project')],['Message',val('message')]];
 const subject='Kaurivo website enquiry: '+val('company').replace(/[\r\n]/g,' ').slice(0,100);
 const body=data.map(x=>x[0]+': '+x[1]).join('\n\n');
 const a=document.createElement('a');
 a.href='mailto:hello.kaurivo@gmail.com?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
 const status=document.querySelector('.form-status');
 if(status)status.textContent='Your email application should open with a draft. Review it and click Send there. This website has not sent anything.';
 a.click();
});
})();
