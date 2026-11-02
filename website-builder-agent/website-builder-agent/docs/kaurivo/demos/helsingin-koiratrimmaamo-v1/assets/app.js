(()=>{'use strict';
const button=document.querySelector('[data-menu-toggle]');
const mobile=document.querySelector('[data-mobile-nav]');
if(button&&mobile){
const close=()=>{mobile.classList.remove('open');document.body.classList.remove('menu-open');button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','Avaa valikko');};
button.addEventListener('click',()=>{const opened=mobile.classList.contains('open');if(opened){close();return;}mobile.classList.add('open');document.body.classList.add('menu-open');button.setAttribute('aria-expanded','true');button.setAttribute('aria-label','Sulje valikko');const first=mobile.querySelector('a');if(first)first.focus();});
mobile.querySelectorAll('a').forEach(link=>link.addEventListener('click',close));
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&mobile.classList.contains('open')){close();button.focus();}});
window.addEventListener('resize',()=>{if(window.innerWidth>1030)close();});
}
if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches&&'IntersectionObserver'in window){
const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('shown');observer.unobserve(entry.target);}});},{threshold:.09});
document.querySelectorAll('.reveal').forEach(element=>{element.classList.add('pending');observer.observe(element);});
}
})();
