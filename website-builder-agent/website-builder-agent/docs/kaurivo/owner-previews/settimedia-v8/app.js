
document.addEventListener('DOMContentLoaded',()=>{
const b=document.querySelector('.menu-toggle'),n=document.querySelector('.nav');
if(b&&n){b.addEventListener('click',()=>{const open=n.classList.toggle('open');b.setAttribute('aria-expanded',String(open));b.textContent=open?'Sulje valikko':'Valikko'});n.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{n.classList.remove('open');b.setAttribute('aria-expanded','false');b.textContent='Valikko'}));}
if(window.matchMedia('(prefers-reduced-motion: reduce)').matches||!('IntersectionObserver' in window)){document.querySelectorAll('.reveal').forEach(e=>e.classList.add('visible'));return;}
const ob=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');ob.unobserve(e.target)}})},{threshold:.08,rootMargin:'0px 0px -35px 0px'});
document.querySelectorAll('.reveal').forEach(e=>ob.observe(e));
});
