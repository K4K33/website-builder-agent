(()=>{"use strict";
const API="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-kotifixi-v17-edit-pilot";
const keys=["hero_heading","hero_intro","services_heading","service1_title","service1_description","service2_title","service2_description","service3_title","service3_description","lawn_price","cleaning_price","closing_heading"];
function apply(data){
 keys.forEach(key=>{if(typeof data[key]==="string")
 document.querySelectorAll('[data-edit-field="'+key+'"]').forEach(el=>el.textContent=data[key]);});
 if(typeof data.hero_image==="string" && /^https:\/\//.test(data.hero_image))
  document.querySelectorAll('[data-edit-image="hero_image"]').forEach(img=>{img.src=data.hero_image;img.removeAttribute("srcset");});
 if(typeof data.email==="string" && /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(data.email)){
  document.querySelectorAll('a[href^="mailto:"]').forEach(a=>{a.href="mailto:"+data.email;if(a.textContent.includes("@"))a.textContent=data.email;});
 }
 if(typeof data.phone_display==="string" && /^\+?[\d\s()-]{6,32}$/.test(data.phone_display)){
  const digits=data.phone_display.replace(/[^\d+]/g,""), dial=digits.startsWith("0")?"+358"+digits.slice(1):digits;
  if(/^\+[0-9]{6,17}$/.test(dial))document.querySelectorAll('a[href^="tel:"]').forEach(a=>{
   a.href="tel:"+dial;
   const n=a.querySelector(".phone-number");
   if(n)n.textContent=data.phone_display;
   else if(a.classList.contains("contact-option")){const b=a.querySelector("strong");if(b)b.textContent=data.phone_display;}
   else if(a.textContent.startsWith("Soita "))a.textContent="Soita "+data.phone_display;
   else if(a.textContent.trim()==="044 363 2429")a.textContent=data.phone_display;
  });
 }
 if(typeof data.hours==="string"){
  document.querySelectorAll(".footer-column > span,.contact-availability strong").forEach(el=>{
   if(el.textContent.includes("10.00"))el.textContent=data.hours;
  });
 }
}
fetch(API+"?action=public",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("not available");return r.json()})
.then(j=>{if(j.ok && j.content)apply(j.content)}).catch(()=>{});
})();