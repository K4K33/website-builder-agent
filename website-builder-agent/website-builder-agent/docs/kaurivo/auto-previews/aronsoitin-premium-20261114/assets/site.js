
(function(){
  "use strict";
  const menu=document.querySelector(".menu-toggle"),nav=document.querySelector(".primary-nav");
  if(menu&&nav){
    menu.addEventListener("click",()=>{
      const opening=!nav.classList.contains("is-open");
      nav.classList.toggle("is-open",opening);
      menu.setAttribute("aria-expanded",String(opening));
      menu.setAttribute("aria-label",opening?"Sulje valikko":"Avaa valikko");
    });
    nav.querySelectorAll("a").forEach(link=>link.addEventListener("click",()=>{
      nav.classList.remove("is-open");menu.setAttribute("aria-expanded","false");
    }));
    document.addEventListener("keydown",event=>{
      if(event.key==="Escape"){nav.classList.remove("is-open");menu.setAttribute("aria-expanded","false");}
    });
  }
  const reveal=document.querySelectorAll("[data-reveal]");
  if("IntersectionObserver" in window&&!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
    const observer=new IntersectionObserver(entries=>{
      for(const entry of entries)if(entry.isIntersecting){
        entry.target.classList.add("visible");observer.unobserve(entry.target);
      }
    },{threshold:.12});
    reveal.forEach(el=>observer.observe(el));
  }else reveal.forEach(el=>el.classList.add("visible"));

  const search=document.querySelector("#product-search");
  const resultCount=document.querySelector("#result-count");
  const chips=[...document.querySelectorAll("[data-product-filter]")];
  const sorter=document.querySelector("#product-sort");
  const grid=document.querySelector("#shop-grid");
  const noResults=document.querySelector("#no-results");
  let filter="all";
  if(grid){
    const cards=[...grid.querySelectorAll("[data-product]")];
    const update=()=>{
      const input=(search?.value||"").toLocaleLowerCase("fi").trim();
      let shown=0;
      for(const card of cards){
        const matchesGroup=filter==="all"||(card.dataset.category||"").split(" ").includes(filter);
        const matchesText=((card.dataset.search||"")+" "+card.textContent).toLocaleLowerCase("fi").includes(input);
        const show=matchesGroup&&matchesText;card.hidden=!show;
        if(show)shown++;
      }
      if(resultCount)resultCount.textContent=shown+" tuotetta esillä";
      if(noResults)noResults.hidden=shown>0;
    };
    if(search)search.addEventListener("input",update);
    for(const chip of chips)chip.addEventListener("click",()=>{
      filter=chip.dataset.productFilter||"all";
      chips.forEach(btn=>btn.setAttribute("aria-pressed",String(btn===chip)));
      update();
    });
    if(sorter)sorter.addEventListener("change",()=>{
      const sorted=[...cards].sort((a,b)=>{
        if(sorter.value==="price-asc")return (+a.dataset.price||0)-(+b.dataset.price||0);
        if(sorter.value==="price-desc")return (+b.dataset.price||0)-(+a.dataset.price||0);
        return (+a.dataset.order||0)-(+b.dataset.order||0);
      });
      sorted.forEach(card=>grid.append(card));update();
    });
    update();
  }
  // No payment, cart or business-mail form is simulated in the owner preview.
  // Product links lead to the real company-operated Shopify checkout flow.
  document.querySelectorAll('a[href^="https://www.aronsoitin.com"],a[href^="https://www.aronsoitin.fi"]').forEach(a=>{
    a.setAttribute("rel","noopener noreferrer");
    a.setAttribute("target","_blank");
  });
})();
