(() => {
  "use strict";
  const h=document.getElementById("site-header"),m=document.getElementById("menu-toggle");
  if(h&&m){
    const set=open=>{h.classList.toggle("menu-open",open);m.setAttribute("aria-expanded",String(open));m.setAttribute("aria-label",open?"Sulje navigaatio":"Avaa navigaatio")};
    m.addEventListener("click",()=>set(!h.classList.contains("menu-open")));
    document.addEventListener("keydown",e=>{if(e.key==="Escape")set(false)});
    h.querySelectorAll("nav a").forEach(a=>a.addEventListener("click",()=>set(false)));
  }
  document.querySelectorAll(".comparison").forEach(box=>{
    const slider=box.querySelector('input[type="range"]');
    if(slider){const update=()=>box.style.setProperty("--split",slider.value+"%");slider.addEventListener("input",update);update()}
  });
  const buttons=[...document.querySelectorAll("button[data-filter]")],cards=[...document.querySelectorAll(".gallery-item[data-kind]")];
  buttons.forEach(b=>b.addEventListener("click",()=>{
    buttons.forEach(x=>x.setAttribute("aria-pressed",String(x===b)));
    cards.forEach(c=>c.hidden=b.dataset.filter!=="kaikki"&&c.dataset.kind!==b.dataset.filter);
  }));
})();