/* Kaurivo demo-job panel. Private rows are loaded with the existing admin RLS
   session. The browser cannot write job statuses, QA records or preview URLs.
   An internal preview is NEVER a client-approved deliverable. */
(function(){
 "use strict";
 const ACTIVE=new Set(["queued","researching","building","qa","publishing"]);
 const ERROR_LABELS={
  free_ai_key_missing:"Ilmaisen rakennusmallin API-avain puuttuu",
  exact_free_model_required:"Ilmaiset Builder- ja QA-mallit pitää määrittää",
  free_model_not_configured:"Ilmainen mallipalvelu ei ole valmis",
  source_website_needs_verification:"Verkkosivun puuttuminen ja yrityksen faktat vaativat vahvistuksen",
  source_dns_not_public:"Alkuperäinen osoite ei ole turvallisesti saavutettavissa",
  research_failed:"Lähdesivun tutkimus ei läpäissyt vaatimuksia",
  researching_failed:"Tutkimus ei läpäissyt vaatimuksia – tarkista yrityksen lähdesivun sisältö",
  source_research_incomplete:"Lähdesivun palvelu- ja brändiaineisto on puutteellinen",
  free_ai_rate_limit:"Ilmaisen tekoälypalvelun päivä- tai minuuttiraja täyttyi",
  free_ai_access_rejected:"Ilmainen tekoälypalvelu hylkäsi API-tunnistuksen",
  free_ai_account_blocked:"Mallipalvelun tili ei salli edes ilmaista pyyntöä",
  free_model_unavailable:"Valittu ilmainen AI-malli ei ole saatavilla",
  free_model_request_rejected:"Ilmainen AI-malli ei hyväksynyt pyynnön muotoa",
  missing_runtime_dependency:"Rakennusympäristöstä puuttuu ohjelmistoriippuvuus",
  research_network_unavailable:"Alkuperäisen sivun tutkiminen epäonnistui verkkoyhteyden takia",
  network_unavailable:"Rakennuksen verkkoyhteys epäonnistui",
  free_ai_response_truncated:"Ilmaisen AI-mallin vastaus katkesi kesken",
  building_failed:"Konsepti tai sivustorakennus ei läpäissyt vaatimuksia",
  qa_failed:"Sivuston laatutarkistus ei läpäissyt vaatimuksia",
  quality_gate_not_approved:"Laadun hyväksyntää ei ole saavutettu",
  premium_interaction_blocked:"Interaktiivinen ominaisuus ei täytä uusimpia laatustandardeja",
  remote_image_rights_not_proven:"Ulkoisten kuvien oikeuksia ei ole vahvistettu",
  runner_stale_timeout:"Rakennustyö katkesi ja vaatii uuden tarkistuksen",
  runner_setup_failed:"Rakennuksen automaatio ei käynnistynyt oikein",
  render_not_serving_exact_release:"Julkaisupalvelin ei palauttanut oikeaa uutta versiota",
  public_assets_broken:"Julkaistun sivuston kuvat tai tyylit eivät latautuneet",
  public_visual_smoke_failed:"Julkaistu sivusto ei läpäissyt todellista selaintarkistusta",
  unexpected_worker_error:"Rakennuksessa tapahtui tekninen virhe"
 };
 const STATUS={
  queued:"Jonossa",researching:"Taustatutkimus",building:"Rakenteilla",
  qa:"Laatutarkistus",publishing:"Julkaisutarkistus",
  internal_preview:"Sisäinen esikatselu",hold:"Odottaa korjausta",failed:"Virhe"
 };
 const $=id=>document.getElementById(id);
 const element=(tag,cls,content)=>{
  const node=document.createElement(tag);
  if(cls)node.className=cls;
  if(content!==undefined)node.textContent=String(content);
  return node;
 };
 function append(parent,tag,cls,text){
  const e=element(tag,cls,text);parent.append(e);return e;
 }
 function validUrl(value,kind){
  try{
   const uri=new URL(value);
   if(!["https:","http:"].includes(uri.protocol)||uri.username||uri.password)return null;
   if(kind&&uri.protocol!=="https:")return null;
   if(kind==="preview"&&uri.hostname!=="k4k33.github.io"&&
      !/^[a-z0-9-]+[.]onrender[.]com$/i.test(uri.hostname))return null;
   if(kind==="qa"&&!(uri.hostname==="github.com"&&
      /^\/K4K33\/website-builder-agent\/actions\/runs\/[0-9]+$/.test(uri.pathname)))return null;
   return uri.href;
  }catch(_){return null;}
 }
 function external(parent,title,value,kind){
  const href=validUrl(value,kind);
  if(!href)return false;
  const link=append(parent,"a","small-action demo-external",title);
  link.href=href;link.target="_blank";link.rel="noopener noreferrer";
  return true;
 }
 function isActive(job){return job&&ACTIVE.has(job.status);}
 function canShowPreview(job){
  return job.status==="internal_preview"&&
   /^[0-9a-f]{40}$/.test(job.release_sha||"")&&
   validUrl(job.preview_url,"preview")&&validUrl(job.qa_url,"qa");
 }
 function card(target,job){
  const row=append(target,"article","record demo-record");
  const main=append(row,"div","record-main");
  append(main,"div","record-title",job.company_name||"Tuntematon yritys");
  const date=job.created_at?new Date(job.created_at).toLocaleString("fi-FI"):"";
  append(main,"div","record-sub",(job.business_id||"—")+" · "+date);
  append(main,"div","record-sub",job.progress||STATUS[job.status]||"Odottaa");
  if(job.error_code)append(main,"div","record-warning","Korjausta vaativa vaihe: "+(ERROR_LABELS[job.error_code]||"Työ vaatii lisätarkistuksen")+" ("+job.error_code+")");
  const actions=append(row,"div","record-actions");
  const badge=append(actions,"span","tag "+(job.status==="internal_preview"?"tag-won":""),STATUS[job.status]||"Tarkistettava");
  badge.setAttribute("aria-label","Työn tila");
  if(job.original_url){
   if(!external(actions,"Vanha sivu",job.original_url))append(main,"div","record-warning","Alkuperäinen sivulinkki on tarkistettava.");
  }else append(main,"div","record-sub","Alkuperäistä verkkosivua ei ole vahvistettu.");
  if(canShowPreview(job)){
   external(actions,"Avaa uusi demo",job.preview_url,"preview");
   external(actions,"QA-raportti",job.qa_url,"qa");
   append(main,"div","record-sub","Suora avattava sisäinen esikatselu. Ei vielä hyväksytty asiakkaalle.");
  }else if(job.status==="internal_preview"){
   append(main,"div","record-warning","Julkaisutodiste on puutteellinen. Uutta linkkiä ei näytetä.");
  }else if(isActive(job)){
   append(main,"div","record-sub","Uusi linkki näytetään vasta aidon julkaisun ja selaintarkistuksen jälkeen.");
  }
  if(job.github_run_url)external(actions,"Rakennuksen loki",job.github_run_url,"qa");
 }
 function render(jobs){
  const all=Array.isArray(jobs)?jobs:[];
  const ready=all.filter(canShowPreview);
  const active=all.filter(isActive);
  const held=all.filter(j=>j.status==="failed"||j.status==="hold"||
    (j.status==="internal_preview"&&!canShowPreview(j)));
  const summary=$("demo-summary");
  if(summary)summary.textContent=ready.length+" sisäistä esikatselua · "+
      active.length+" työn alla · "+held.length+" odottaa korjausta";
  for(const [id,items,missing] of [
   ["demo-ready-list",ready,"Ei vielä julkaistuja ja teknisesti tarkistettuja demoja."],
   ["demo-running-list",active,"Ei tällä hetkellä rakennettavia demoja."],
   ["demo-hold-list",held,"Ei pysähtyneitä tai hylättyjä rakennustöitä."]
  ]){
   const el=$(id);if(!el)continue;
   el.replaceChildren();
   if(!items.length)append(el,"div","empty",missing);
   else items.forEach(job=>card(el,job));
  }
 }
 async function start(candidate,{db,jobs,reload,showTab,toast}){
  if(!candidate||!candidate.id||!db){toast("Kirjaudu uudelleen ja valitse yritys.","error");return;}
  const active=(jobs||[]).find(j=>j.prospect_id===candidate.id&&isActive(j));
  if(active){showTab("demos");return;}
  try{
   const {data,error}=await db.rpc("kaurivo_request_demo_build",{p_prospect_id:candidate.id});
   if(error)throw error;
   if(!data)throw Error("Rakennustyön tunnistetta ei saatu.");
   await reload();
   showTab("demos");
   toast("Demon rakentaminen lisättiin työjonoon. Seuraa etenemistä tässä näkymässä.","success");
  }catch(e){
   const message=String(e.message||"Tuntematon virhe");
   const human=message.includes("daily free-build")?"Maksuttomien rakennuspyyntöjen päiväkohtainen raja (5) tuli vastaan."
    :message.includes("website URL must")?"Yrityksen nykyinen verkkosivulinkki on tarkistettava."
    :message.includes("opted out")?"Markkinointikiellon tehneen yrityksen työ vaatii manuaalisen käsittelyn."
    :message.includes("skipped")?"Ohitetun yrityksen tila on muutettava ennen rakentamista.":message;
   toast("Rakennustyötä ei käynnistetty: "+human,"error");
  }
 }
 window.KaurivoDemoJobs=Object.freeze({render,start,isActive});
})();