(()=>{
"use strict";
const API="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-kotifixi-v17-edit-pilot";
const KEY="kaurivo_kotifixi_v17_editor";
const form=document.getElementById("edit-form"),status=document.getElementById("status");
const editor=document.getElementById("editor"),missing=document.getElementById("missing");
const verEl=document.getElementById("current-version"),historyEl=document.getElementById("history");
const fieldNodes=[...form.querySelectorAll("[data-field]")];
let token="",version=0,content={};
function show(t,kind=""){status.textContent=t;status.dataset.type=kind}
function busy(flag){for(const id of ["save","upload","restore"])document.getElementById(id).disabled=flag}
const fragment=new URLSearchParams(location.hash.replace(/^#/,""));
if(fragment.has("edit")){
 const value=fragment.get("edit")||"";
 if(/^[A-Za-z0-9_-]{40,100}$/.test(value)){
  sessionStorage.setItem(KEY,value);
  history.replaceState(null,"",location.pathname+location.search);
 }
}
token=sessionStorage.getItem(KEY)||"";
if(!token){missing.hidden=false;return}
editor.hidden=false;
function fill(c){
 content={...c};
 for(const el of fieldNodes){el.value=typeof content[el.dataset.field]==="string"?content[el.dataset.field]:""}
}
function collect(){
 const next={...content};
 for(const el of fieldNodes)next[el.dataset.field]=el.value.trim();
 return next;
}
async function post(action,details={}){
 const response=await fetch(API,{
  method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify(Object.assign({action,token},details)),cache:"no-store",referrerPolicy:"no-referrer"
 });
 const obj=await response.json().catch(()=>({error:"Tuntematon palvelinvirhe"}));
 if(!response.ok||obj.ok!==true)throw Error(obj.error||"Palvelin ei vahvistanut muutosta");
 return obj;
}
async function historyList(){
 const response=await post("history");
 historyEl.replaceChildren();
 for(const record of response.history||[]){
  const item=document.createElement("option");
  item.value=String(record.version);
  item.textContent="Versio "+record.version+" · "+new Date(record.saved_at).toLocaleString("fi-FI");
  historyEl.append(item);
 }
}
function updatePreview(){
 document.getElementById("preview").src="../?revision="+encodeURIComponent(version);
}
async function load(){
 busy(true);show("Ladataan tallennettu sisältö…");
 try{
  const response=await fetch(API+"?action=public",{cache:"no-store"});
  if(!response.ok)throw Error("Yhteys sisältöpalveluun epäonnistui");
  const result=await response.json();
  if(!result.ok||!result.content)throw Error("Sisältöä ei löytynyt");
  fill(result.content);
  version=result.version;
  verEl.textContent="Versio "+version;
  await historyList();
  show("Muokkaa kenttiä ja tallenna. Sivusto päivittyy tallennuksen jälkeen.","ok");
 }catch(error){show("Lataus epäonnistui: "+String(error.message||error),"error")}
 finally{busy(false)}
}
form.addEventListener("submit",async(event)=>{
 event.preventDefault();
 if(!form.reportValidity())return;
 const next=collect();
 if(!/^https:\/\//.test(next.hero_image)){show("Kuvan osoitteen pitää alkaa https://","error");return}
 busy(true);show("Tallennetaan testisivulle…");
 try{
  const result=await post("save",{expected_version:version,content:next});
  fill(result.content);version=result.version;verEl.textContent="Versio "+version;
  updatePreview();await historyList();
  show("Tallennus onnistui. Muutos näkyy testisivuston esikatselussa.","ok");
 }catch(error){
  const t=String(error.message||error);
  show(t.includes("version_conflict")?"Sivua muokattiin toisessa ikkunassa. Lataa uusin versio ja yritä uudelleen.":"Tallennus ei onnistunut: "+t,"error");
 }finally{busy(false)}
});
document.getElementById("reload").addEventListener("click",load);
document.getElementById("restore").addEventListener("click",async()=>{
 const previous=Number(historyEl.value);
 if(!previous||previous===version)return;
 if(!confirm("Palautetaanko versio "+previous+"? Nykyinen säilyy historiassa."))return;
 busy(true);show("Palautetaan vanhaa versiota…");
 try{
  const result=await post("restore",{restore_version:previous,expected_version:version});
  version=result.version;fill(result.content);verEl.textContent="Versio "+version;
  updatePreview();await historyList();show("Aiempi versio palautettiin onnistuneesti.","ok");
 }catch(error){show("Palautus epäonnistui: "+String(error.message||error),"error")}
 finally{busy(false)}
});
document.getElementById("upload").addEventListener("click",async()=>{
 const chosen=document.getElementById("photo").files[0];
 if(!chosen){show("Valitse ensin JPG-, PNG- tai WebP-kuva.","error");return}
 if(chosen.size>1500000||chosen.size<16||!["image/png","image/jpeg","image/webp"].includes(chosen.type)){
  show("Kuvan koko saa olla enintään 1,5 Mt ja muoto JPG, PNG tai WebP.","error");return;
 }
 busy(true);show("Lisätään kuvaa testisivulle…");
 try{
  const encoded=await new Promise((resolve,reject)=>{
   const reader=new FileReader();
   reader.onload=()=>resolve(String(reader.result).split(",")[1]);
   reader.onerror=()=>reject(Error("Kuvan lukeminen epäonnistui"));
   reader.readAsDataURL(chosen);
  });
  const result=await post("upload",{mime:chosen.type,data:encoded});
  form.querySelector('[data-field="hero_image"]').value=result.url;
  show("Kuva lisättiin. Paina Tallenna testisivulle, jotta se näkyy sivustolla.","ok");
 }catch(error){show("Kuvan lisäys epäonnistui: "+String(error.message||error),"error")}
 finally{busy(false)}
});
load();
})();