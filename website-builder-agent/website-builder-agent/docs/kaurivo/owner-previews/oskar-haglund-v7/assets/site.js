/* Source-limited multilingual Kaurivo concept, no telemetry or backend. */
(function(){
 "use strict";
 const root=document.documentElement;
 const translations={sv:{
  menu:"Meny",close:"Stäng meny",
  subject:"Transportförfrågan – Ab Oskar Haglund Oy",
  preface:"Hej! Jag vill ställa en fråga om vägtransport.",
  from:"Avhämtningsort",to:"Destination",goods:"Gods / omfattning",date:"Önskad tidpunkt",details:"Övriga uppgifter",
  footer:"Detta är ett e-postutkast och skickas inte automatiskt."
 },fi:{
  menu:"Valikko",close:"Sulje valikko",
  subject:"Kuljetustiedustelu – Ab Oskar Haglund Oy",
  preface:"Hei! Haluaisin tiedustella maantiekuljetuksesta.",
  from:"Noutopaikka",to:"Määränpää",goods:"Kuljetettava tavara / määrä",date:"Toivottu ajankohta",details:"Lisätiedot",
  footer:"Tämä on sähköpostiluonnos. Viestiä ei lähetetä automaattisesti."
 }};
 const langButtons=[...document.querySelectorAll("[data-set-lang]")];
 const stored=(()=>{try{return localStorage.getItem("oskar-haglund-v7-lang")}catch(_){return null}})();
 let language=stored==="fi"?"fi":"sv";
 function setLang(lang){
  language=lang==="fi"?"fi":"sv";root.lang=language;
  for(const el of document.querySelectorAll("[data-lang]")){
   el.hidden=el.getAttribute("data-lang")!==language;
  }
  for(const button of langButtons){
   button.setAttribute("aria-pressed",String(button.dataset.setLang===language));
  }
  const pageTitle=root.getAttribute("data-title-"+language);
  if(pageTitle)document.title=pageTitle;
  for(const toggle of document.querySelectorAll("[data-menu-toggle]")){
   if(toggle.getAttribute("aria-expanded")==="true"){
    toggle.setAttribute("aria-label",translations[language].close);
   }else{
    toggle.setAttribute("aria-label",translations[language].menu);
   }
  }
  try{localStorage.setItem("oskar-haglund-v7-lang",language)}catch(_){}
 }
 langButtons.forEach(button=>button.addEventListener("click",()=>setLang(button.dataset.setLang)));
 const toggles=[...document.querySelectorAll("[data-menu-toggle]")];
 const drawer=document.querySelector("[data-mobile-drawer]");
 function setMenu(open){
  if(!drawer)return;
  drawer.hidden=!open;
  toggles.forEach(b=>{
   b.setAttribute("aria-expanded",String(open));
   b.setAttribute("aria-label",open?translations[language].close:translations[language].menu);
  });
 }
 toggles.forEach(b=>b.addEventListener("click",()=>setMenu(drawer?.hidden??true)));
 drawer?.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>setMenu(false)));
 document.addEventListener("keydown",e=>{if(e.key==="Escape")setMenu(false)});
 const mq=window.matchMedia("(min-width: 821px)");
 mq.addEventListener?.("change",e=>{if(e.matches)setMenu(false)});
 const mail=document.querySelector("[data-email-builder]");
 if(mail){
  mail.addEventListener("submit",event=>{
   event.preventDefault();
   const form=new FormData(mail);
   const data=translations[language];
   const fields=[["from","from"],["to","to"],["goods","goods"],["date","date"],["details","details"]];
   const message=[data.preface,"",...fields.map(([key,label])=>data[label]+": "+String(form.get(key)||"").trim()),"",data.footer].join("\n");
   const address="info@oskarhaglund.fi";
   const url="mailto:"+address+"?subject="+encodeURIComponent(data.subject)+"&body="+encodeURIComponent(message);
   window.location.href=url;
   const note=document.querySelector("[data-draft-feedback]");
   if(note){note.hidden=false;note.textContent=data.footer}
  });
 }
 setLang(language);
})();
