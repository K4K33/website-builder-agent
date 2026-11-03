
(() => {
 const toggle=document.querySelector('[data-menu-toggle]');
 const menu=document.querySelector('[data-menu]');
 if(toggle&&menu){toggle.addEventListener('click',()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'Sulje':'Valikko';menu.classList.toggle('is-open',open);menu.hidden=!open;});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!menu.hidden){menu.hidden=true;menu.classList.remove('is-open');toggle.textContent='Valikko';toggle.setAttribute('aria-expanded','false');toggle.focus();}})}
})();
