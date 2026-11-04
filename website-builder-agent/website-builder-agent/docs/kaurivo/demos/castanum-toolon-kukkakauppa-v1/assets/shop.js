(() => {
  "use strict";
  const grid=document.getElementById("store-grid");
  if(!grid)return;
  const items=[...grid.querySelectorAll(".store-product-card")];
  const filters=[...document.querySelectorAll("[data-shop-filter]")];
  const search=document.querySelector("[data-shop-search]");
  const sorting=document.querySelector("[data-shop-sort]");
  const more=document.querySelector("[data-shop-more]");
  const counter=document.querySelector("[data-shop-counter]");
  const moreArea=document.querySelector(".store-more");
  const empty=document.createElement("p");
  empty.className="store-empty";
  empty.textContent="Hakua vastaavia tuotteita ei löytynyt. Katso koko valikoima eKukasta.";
  empty.hidden=true;
  grid.after(empty);
  let category="all",term="",sort="default",limit=12;

  function refresh(){
    const selected=items.filter(item=>{
      const matchesCategory=category==="all"||item.dataset.category===category;
      const name=(item.dataset.search||"").normalize("NFC");
      return matchesCategory&&name.includes(term);
    });
    selected.sort((a,b)=>{
      if(sort==="price-asc")return Number(a.dataset.price)-Number(b.dataset.price);
      if(sort==="price-desc")return Number(b.dataset.price)-Number(a.dataset.price);
      if(sort==="name")return (a.dataset.search||"").localeCompare(b.dataset.search||"","fi");
      return items.indexOf(a)-items.indexOf(b);
    });
    const visible=selected.slice(0,limit);
    grid.append(...items.filter(item=>!selected.includes(item)),...selected);
    const showing=new Set(visible);
    items.forEach(item=>{item.hidden=!showing.has(item);});
    counter.textContent=visible.length+" / "+selected.length+" tuotetta näkyvissä";
    empty.hidden=selected.length!==0;
    if(moreArea)moreArea.hidden=selected.length<=limit;
  }

  filters.forEach(button=>button.addEventListener("click",()=>{
    category=button.dataset.shopFilter||"all";
    filters.forEach(b=>b.setAttribute("aria-pressed",String(b===button)));
    limit=12;
    refresh();
  }));
  if(search)search.addEventListener("input",()=>{
    term=search.value.toLocaleLowerCase("fi").normalize("NFC").trim();
    limit=12;refresh();
  });
  if(sorting)sorting.addEventListener("change",()=>{
    sort=sorting.value;refresh();
  });
  if(more)more.addEventListener("click",()=>{limit+=12;refresh();});
  refresh();
})();