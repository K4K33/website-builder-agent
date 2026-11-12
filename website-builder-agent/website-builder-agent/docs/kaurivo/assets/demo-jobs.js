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
  source_http_access_blocked:"Yrityksen alkuperäinen sivusto esti automaattisen lukemisen (401/403). Tarvitaan erillinen lähdeaineiston tarkistus.",
  source_http_rate_limited:"Alkuperäinen sivusto rajoitti automaattista hakua. Vältä jatkuvia uudelleenyrityksiä.",
  source_website_unreachable:"Alkuperäinen sivu ei vastannut rakennusagentin tutkimuspyyntöön.",
  free_ai_rate_limit:"Ilmaisen tekoälypalvelun päivä- tai minuuttiraja täyttyi",
  free_ai_capacity_unavailable:"Ilmainen OpenRouter-kiintiö tai palveluntarjoajan kapasiteetti loppui. Työ jatkuu seuraavana sallittuna käyttöpäivänä ilman maksullista mallia.",
  free_ai_access_rejected:"Ilmainen tekoälypalvelu hylkäsi API-tunnistuksen",
  free_ai_key_invalid:"OpenRouterin API-avain ei kelpaa tai se on vanhentunut. Päivitä GitHubin OPENROUTER_API_KEY.",
  free_ai_key_forbidden:"OpenRouter esti mallipyynnön (403). Tarkista API-avaimen oikeudet ja tilin suojausasetukset.",
  free_ai_wrong_key_type:"OpenRouteriin on asetettu hallinta-avain, joka ei käy mallikutsuihin.",
  free_ai_key_validation_unavailable:"OpenRouterin avaimen tarkistuspalvelu ei vastannut.",
  free_ai_key_metadata_invalid:"OpenRouter palautti virheellisen avaimen tarkistusvastauksen.",
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
 const GITHUB_WORKFLOW="https://github.com/K4K33/website-builder-agent/actions/workflows/kaurivo-demo-worker.yml";
 const DISPATCH_MESSAGES={
  github_token_not_configured:"GitHubin suoran käynnistyksen avain puuttuu Supabasesta.",
  github_token_permissions:"GitHubin käynnistysavaimelta puuttuu Actions:write-oikeus tai se ei kelpaa.",
  github_rate_limited:"GitHub rajoitti käynnistyspyyntöjä.",
  github_unreachable:"GitHubiin ei saatu yhteyttä.",
  already_requested_or_not_queued:"Käynnistystä on jo pyydetty tai työ on jo käynnissä.",
  admin_queued_job_required:"Rakennuspyyntö ei ole enää jonossa tai kirjautuminen ei oikeuta käynnistystä.",
  db_unavailable:"Tietokantayhteys ei vastannut, eikä GitHub-käynnistystä lähetetty.",
  backend_unavailable:"Supabasen käynnistyspalvelun asetukset puuttuvat.",
  dispatch_claim_failed:"Rakennuksen käynnistysvarausta ei saatu tietokannasta.",
  github_dispatch_failed:"GitHub hylkäsi käynnistyspyynnön.",
  github_dispatch_unavailable:"GitHub-käynnistyspalvelusta ei saatu vahvistusta.",
  dispatch_client_unavailable:"Kirjautumista tai käynnistysasiakasta ei saatu käyttöön."
 };
 async function dispatchNow(db,jobId){
  if(!db?.functions?.invoke)return {ok:false,reason:"dispatch_client_unavailable"};
  try{
   const {data,error}=await db.functions.invoke("kaurivo-demo-dispatch",{
    body:{job_id:jobId}
   });
   if(error){
    // supabase-js normally returns data=null on a 4xx/5xx Edge response.
    // Read the authenticated HTTP error body to expose its allowlisted code.
    let reason=data?.reason;
    try{
     if(!reason && typeof error.context?.json==="function"){
      const body=await error.context.json();
      reason=body?.reason;
     }
    }catch(_){/* Non-JSON transport failure: no fabricated success. */}
    return {ok:false,reason:typeof reason==="string"?reason:"github_dispatch_unavailable"};
   }
   if(data?.ok===true&&["local_ready","local_waiting","local_running"].includes(
       data.dispatch)){
    return {ok:true,local:true,running:data.dispatch==="local_running",
      waiting:data.dispatch==="local_waiting"};
   }
   return data?.ok===true&&data.dispatch==="accepted"?
      {ok:true,local:false}:{ok:false,reason:data?.reason||"github_dispatch_unavailable"};
  }catch(_){return {ok:false,reason:"github_dispatch_unavailable"};}
 }
 function dispatchFeedback(result,toast){
  if(result.ok){
   toast(result.local?
     result.running?"Windows-rakentaja on jo aloittanut demon tutkimisen.":
     result.waiting?"Windows on valmiina, mutta pikailmoitusta ei voitu vahvistaa. Varatarkistus jatkuu automaattisesti.":
     "Windows-rakentajalle lähetettiin pikailmoitus. Se aloittaa tämän demon suoraan.":
     "GitHub vastaanotti käynnistyspyynnön. Seuraa etenemistä Demot-näkymässä.","success");
   return;
  }
  const explanation=DISPATCH_MESSAGES[result.reason]||"GitHubin käynnistystä ei voitu vahvistaa.";
  toast("Rakennuspyyntö on jonossa. "+explanation+" Käynnistä työntekijä tarvittaessa GitHub Actionsista.","error");
 }
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
   if(kind==="qa"&&!((uri.hostname==="github.com"&&
      /^\/K4K33\/website-builder-agent\/actions\/runs\/[0-9]+$/.test(uri.pathname))||
      (uri.hostname==="kaurivo-auto-demos-2026.onrender.com"&&
       /^\/[a-z0-9-]+\/qa[.]html$/.test(uri.pathname))))return null;
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
 function comparisonLink(group,label,url,kind,emptyLabel){
  const tile=append(group,"div","demo-comparison-tile");
  const href=validUrl(url,kind);
  if(!href){
   append(tile,"span","demo-comparison-label",label);
   append(tile,"span","demo-comparison-empty",emptyLabel);
   return null;
  }
  const a=append(tile,"a","demo-comparison-link",label);
  a.href=href;
  a.target="_blank";
  a.rel="noopener noreferrer";
  // Show the actual host/path so the owner can verify the comparison.
  // Never render URL data as HTML or embed third-party previews in admin.
  const parsed=new URL(href);
  append(tile,"span","demo-comparison-address",
    parsed.hostname+parsed.pathname+(parsed.search?"…":""));
  return href;
 }
 function comparisonLinks(parent,job,options){
  const ready=canShowPreview(job);
  const group=append(parent,"div","demo-comparison");
  group.setAttribute("aria-label","Vanhan ja uuden verkkosivun vertailulinkit");
  const oldHref=comparisonLink(group,"Vanha sivu",job.original_url,null,
    job.original_url?"Vanhan sivun osoitetta ei voitu vahvistaa.":"Ei aiempaa verkkosivua");
  const newHref=comparisonLink(group,"Uusi sivu",ready?job.preview_url:null,"preview",
    job.status==="internal_preview"?"Julkaisun vahvistus puuttuu":
    ACTIVE.has(job.status)?"Uusi sivu valmistuu laatutarkistuksen jälkeen":
    "Uutta sivua ei ole vielä hyväksytysti julkaistu");
  if(oldHref&&newHref){
   const copy=append(parent,"button","small-action demo-copy-comparison","Kopioi molemmat linkit");
   copy.type="button";
   copy.addEventListener("click",async()=>{
    try{
     if(!navigator.clipboard||typeof navigator.clipboard.writeText!=="function")
      throw Error("clipboard_unavailable");
     await navigator.clipboard.writeText(
      String(job.company_name||"Yritys")+"\n"+
      "Vanha sivu: "+oldHref+"\n"+
      "Uusi sivu: "+newHref);
     if(options?.toast)options.toast("Molemmat sivulinkit kopioitu.","success");
    }catch(_){
     if(options?.toast)options.toast("Linkkien kopiointi ei onnistunut. Avaa linkit suoraan niiden otsikoista.","error");
    }
   });
  }
  if(!oldHref&&newHref){
   append(parent,"div","record-sub",
    "Yritykselle ei ole vahvistettua vanhaa sivua, joten vertailulinkkiä ei keksitä.");
  }
 }
 function isActive(job){return job&&ACTIVE.has(job.status);}
 function canShowPreview(job){
  return job.status==="internal_preview"&&
   /^[0-9a-f]{40}$/.test(job.release_sha||"")&&
   validUrl(job.preview_url,"preview")&&validUrl(job.qa_url,"qa");
 }
 function card(target,job,options){
  const deferred=job.status==="queued"&&
    Number.isFinite(Date.parse(job.next_eligible_at||""))&&
    Date.parse(job.next_eligible_at)>Date.now();
  const row=append(target,"article","record demo-record");
  const main=append(row,"div","record-main");
  append(main,"div","record-title",job.company_name||"Tuntematon yritys");
  const date=job.created_at?new Date(job.created_at).toLocaleString("fi-FI"):"";
  append(main,"div","record-sub",(job.business_id||"—")+" · "+date);
  const localActive=job.runner_kind==="local"&&job.status!=="queued";
  const awaitingDispatch=job.status==="queued"&&!deferred;
  const dispatchFailure=awaitingDispatch&&job.dispatch_error_code;
  const acceptedAt=Date.parse(job.dispatch_accepted_at||"");
  const startedAt=Date.parse(job.started_at||"");
  // An old dispatch stays recorded when a claimed build returns to the queue.
  const dispatchAccepted=awaitingDispatch&&!dispatchFailure&&Number.isFinite(acceptedAt)&&
    (!Number.isFinite(startedAt)||acceptedAt>startedAt);
  const dispatchElapsed=dispatchAccepted?Date.now()-acceptedAt:0;
  const dispatchStalled=dispatchAccepted&&Number.isFinite(dispatchElapsed)
    &&dispatchElapsed>120000;
  append(main,"div","record-sub",
    dispatchFailure?"GitHub-käynnistys epäonnistui. Rakennus ei ole käynnissä.":
    dispatchStalled?"GitHubille lähetetty käynnistyspyyntö ei ole johtanut vahvistettuun rakennuksen aloitukseen.":
    dispatchAccepted?"Käynnistyspyyntö lähetetty GitHubille. Odotetaan rakennuksen aloitusta.":
    job.progress||STATUS[job.status]||"Odottaa"); 
  if(localActive)append(main,"div","record-sub",
    "Työ suoritetaan omalla Windows-rakentajalla ilman GitHubin suoritusjonoa.");
  if(dispatchStalled){
   append(main,"div","record-warning",
     "GitHubin käynnistyminen on viivästynyt. Painike lähetti pyynnön, mutta rakennustyö ei ole vielä alkanut. Tarkista GitHub Actionsin estot ja laskutusasetukset; toistuva klikkaaminen ei nopeuta sitä.");
  }
  if(dispatchFailure){
   append(main,"div","record-warning",
    (DISPATCH_MESSAGES[job.dispatch_error_code]||"GitHub-käynnistystä ei voitu vahvistaa.")+
    " Työ on tallessa mutta ei käynnissä. Korjaa käynnistysyhteys ja valitse Käynnistä nyt.");
   if(job.dispatch_error_code==="github_token_not_configured"){
    append(main,"div","record-sub",
      "Ylläpidon pitää lisätä KAURIVO_GITHUB_DISPATCH_TOKEN Supabasen Edge Function Secrets -asetuksiin. Tunnusta ei saa kirjoittaa tähän sivuun.");
   }
  }
  if(job.error_code)append(main,"div","record-warning",
    (deferred?"Automaattinen jatkaminen: ":"Korjausta vaativa vaihe: ")+
    (ERROR_LABELS[job.error_code]||"Työ vaatii lisätarkistuksen")+" ("+job.error_code+")");
  if(deferred)append(main,"div","record-sub",
    "Seuraava automaattinen yritys aikaisintaan: "+new Date(job.next_eligible_at).toLocaleString("fi-FI",{
      timeZone:"Europe/Helsinki"
    })+" Suomen aikaa. Vanhat tarkistuspisteet säilyvät.");
  const actions=append(row,"div","record-actions");
  const badge=append(actions,"span","tag "+(job.status==="internal_preview"?"tag-won":""),
    deferred?"Jatkuu automaattisesti":dispatchFailure?"Käynnistys estynyt":
    dispatchStalled?"Aloitus vahvistamatta":
    dispatchAccepted?"Käynnistys lähetetty":STATUS[job.status]||"Tarkistettava");
  badge.setAttribute("aria-label","Työn tila");
  // One consistent, prominent old/new comparison for EVERY automatic
  // demo job, from queue through verified preview. No invented URLs.
  comparisonLinks(main,job,options);
  if(canShowPreview(job)){
   external(actions,"QA-raportti",job.qa_url,"qa");
   append(main,"div","record-sub","Uusi sivu on suora, selaimessa tarkistettu sisäinen esikatselu. Ei vielä hyväksytty asiakkaalle.");
   // Every published demo also carries an explicit CMS/customer handover
   // checklist. A static link is not a WordPress install or edit permission.
   const handover=append(main,"details","demo-handover");
   append(handover,"summary","","Asiakasluovutus · muokattava CMS vielä todentamatta");
   append(handover,"p","record-sub",
     "Demolinkki on sisäinen esikatselu. Luovutus tehdään vasta sopimuksen, asiakkaan oman verkkotunnuksen ja erikseen testatun WordPressin tai muun CMS:n jälkeen.");
   const steps=append(handover,"ul","demo-handover-list");
   for(const step of [
    "Siirrä hyväksytty ulkoasu ja kaikki alisivut asiakkaan hallitsemaan CMS:ään.",
    "Testaa asiakkaan omilla oikeuksilla kirjautuminen ja tekstin, kuvan sekä yhteystietojen muokkaus.",
    "Julkaise muutos ja tarkista mobiili, lomakkeet, animaatiot ja kauppatoiminnot.",
    "Testaa varmuuskopio ja palautus. Anna asiakkaalle kirjalliset muokkausohjeet.",
    "Pyydä asiakkaan hyväksyntä. Vasta tämän jälkeen sivusto on luovutusvalmis."
   ]) append(steps,"li","",step);
  }else if(job.status==="internal_preview"){
   append(main,"div","record-warning","Julkaisutodiste on puutteellinen. Uutta linkkiä ei näytetä.");
  }
  if(job.status==="queued"&&!deferred){
   // Scheduling is a backup, not a guaranteed five-minute service. Attempt
   // private authenticated REST workflow_dispatch and offer owner GH UI as
   // safe fallback when the one-time token has not been configured.
   if(options?.db){
    const kick=append(actions,"button","small-action demo-build-dispatch","Käynnistä nyt");
    kick.type="button";
    kick.addEventListener("click",async()=>{
     kick.disabled=true;
     try{
      const status=await dispatchNow(options.db,job.id);
      if(options.reload)await options.reload();
      dispatchFeedback(status,options.toast);
     }finally{kick.disabled=false;}
    });
   }
   const link=append(actions,"a","small-action demo-gh-manual","GitHubin käynnistys");
   link.href=GITHUB_WORKFLOW;link.target="_blank";link.rel="noopener noreferrer";
   append(main,"div","record-sub","Rakenna demo lähettää käynnistyspyynnön automaattisesti. GitHubin käynnistys on vain varavaihtoehto, jos palvelinyhteys ei toimi. Jonossa olo ei tarkoita käynnissä olevaa työtä.");
  }
  if(job.github_run_url)external(actions,"Rakennuksen loki",job.github_run_url,"qa");
  // A failed job is not permanent. A fresh owner request snapshots the
  // latest corrected website from the prospect record and gets a new job.
  if((job.status==="hold"||job.status==="failed")&&options?.db){
   const retry=append(actions,"button","small-action demo-build-retry","Rakenna uudelleen");
   retry.type="button";
   retry.addEventListener("click",async()=>{
    retry.disabled=true;
    try{
     await start({id:job.prospect_id},{
      db:options.db,jobs:options.jobs,health:options.health,
      reload:options.reload,showTab:options.showTab,toast:options.toast
     });
    }finally{retry.disabled=false;}
   });
  }
 }
 function getHealth(health){
  if(Array.isArray(health))return health[0]||null;
  return health&&typeof health==="object"?health:null;
 }
 // "ok" is an observation by a verified worker, not a promise of completion.
 // A delayed cron does not invalidate that observation for QUEUEING only.
 // Before any AI work the worker validates the actual key again, and the
 // database blocks new inserts when it has an explicit bad/unknown status.
 function healthBlocked(health){
  const item=getHealth(health);
  return !item||item.status!=="ok";
 }
 function healthStale(health){
  const item=getHealth(health);
  if(!item||item.status!=="ok")return false;
  const checked=Date.parse(item.checked_at||"");
  return !Number.isFinite(checked)||Date.now()-checked>2*60*60*1000;
 }
 function healthSummary(health){
  const item=getHealth(health);
  const output=$("demo-health");
  if(!output)return;
  output.replaceChildren();
  output.className="demo-health";
  if(!item){
   append(output,"span","","Rakennuspalvelun terveystilaa ei voitu vahvistaa. Voit lisätä demon jonoon, mutta rakentaminen vaatii toimivan ilmaisen AI-palvelun.");
   return;
  }
  const unavailable=healthBlocked(health);
  const stale=healthStale(health);
  output.classList.add(unavailable?"demo-health-blocked":stale?"demo-health-stale":"demo-health-ready");
  const status=unavailable?"Rakentaja tauolla – uusia pyyntöjä voi lisätä":
    stale?"Tarkistus vanhentunut – voit lisätä työn jonoon":"Rakennuspalvelu käytettävissä";
  append(output,"strong","",status);
  const label=ERROR_LABELS[item.error_code]||"OpenRouterin avaimen tai ajastuksen toimivuus pitää tarkistaa.";
  append(output,"span","",unavailable?label+" Voit silti lisätä uuden demon jonoon, mutta rakentaja tarvitsee toimivan avaimen.":stale?
    "Edellinen avaintarkistus onnistui, mutta GitHubin automaattinen ajo on viivästynyt. Jonoon lisääminen on sallittu; työntekijä tarkistaa avaimen uudelleen ennen rakentamista. Uutta demoa ei näytetä valmiina ennen kaikkia QA- ja julkaisukokeita.":
    "Ilmainen AI-avain on tarkistettu. Lopullinen demovalmius vaatii erillisen rakentamisen ja QA-tarkistuksen.");
  const checked=Date.parse(item.checked_at||"");
  if(Number.isFinite(checked))append(output,"small","","Tarkistettu "+new Date(checked).toLocaleString("fi-FI"));
  const log=validUrl(item.github_run_url,"qa");
  if(log){
    const a=append(output,"a","demo-health-log","GitHubin tarkistus");
    a.href=log;a.target="_blank";a.rel="noopener noreferrer";
  }
 }
 let pendingWindowsToken="";
 function showWindowsToken(host,token,toast){
  host.replaceChildren();
  const guide=append(host,"a","","Windows-rakentajan käyttöönotto-ohje");
  guide.href="https://github.com/K4K33/website-builder-agent/blob/main/website-builder-agent/website-builder-agent/docs/kaurivo/LOCAL_WINDOWS_WORKER.md";
  guide.target="_blank";guide.rel="noopener noreferrer";
  append(host,"strong","","Windows-rakentajan avain luotiin");
  append(host,"span","","Kopioi avain nyt Windowsin asennusohjelmaan. Uusi avain mitätöi aiemman; älä jaa tätä avainta.");
  const input=append(host,"input","demo-local-token");
  input.type="password";input.readOnly=true;input.value=token;
  input.autocomplete="off";input.setAttribute("aria-label","Kertaluonteinen Windows-rakentajan avain");
  const copy=append(host,"button","small-action","Kopioi Windows-avain");
  copy.type="button";
  copy.addEventListener("click",async()=>{
   try{
    if(!navigator.clipboard?.writeText)throw Error("clipboard_unavailable");
    await navigator.clipboard.writeText(token);
    toast("Avain kopioitu. Liitä se Windowsin asennusohjelmaan.","success");
   }catch(_){input.type="text";input.select();
    toast("Kopiointi estyi. Valitse näkyvä avain ja kopioi käsin.","error");}
  });
  const reveal=append(host,"button","small-action","Näytä tai piilota");
  reveal.type="button";
  reveal.addEventListener("click",()=>{input.type=input.type==="password"?"text":"password";});
  const close=append(host,"button","small-action","Piilota avain pysyvästi tästä välilehdestä");
  close.type="button";
  close.addEventListener("click",()=>{
   pendingWindowsToken="";input.value="";host.replaceChildren();
   append(host,"span","","Avain piilotettu. Jos et kopioinut sitä, luo uusi avain.");
  });
 }
 async function enrollWindows(db,toast,host){
  const {data,error}=await db.functions.invoke("kaurivo-local-enroll",{
    body:{action:"enroll"}
  });
  if(error||!data?.ok||!/^kvl_[0-9a-f]{64}$/.test(data.token||"")){
   toast("Windows-tunnuksen luominen ei onnistunut. Tarkista ylläpitäjän kirjautuminen.","error");
   return;
  }
  pendingWindowsToken=data.token;
  showWindowsToken(host,pendingWindowsToken,toast);
 }
 function windowsEnrollment(options){
  const health=$("demo-health");
  if(!health||!options?.db)return;
  const container=append(health,"div","demo-local-enroll");
  // CRM refreshes every few seconds; keep the one-time secret only in this
  // tab's memory until the operator explicitly clears it. No localStorage.
  if(pendingWindowsToken){
   showWindowsToken(container,pendingWindowsToken,options.toast||(()=>{}));
   return;
  }
  const guide=append(container,"a","","Windows-rakentajan käyttöönotto-ohje");
  guide.href="https://github.com/K4K33/website-builder-agent/blob/main/website-builder-agent/website-builder-agent/docs/kaurivo/LOCAL_WINDOWS_WORKER.md";
  guide.target="_blank";guide.rel="noopener noreferrer";
  const button=append(container,"button","small-action","Luo Windows-rakentajan avain");
  button.type="button";
  button.addEventListener("click",async()=>{
   if(!window.confirm("Luo uusi Windows-avain? Aiemman koneen avain lakkaa toimimasta."))
    return;
   button.disabled=true;
   try{await enrollWindows(options.db,options.toast||(()=>{}),container);}
   finally{button.disabled=false;}
  });
 }
 function render(jobs,health,options={}){
  healthSummary(health);
  windowsEnrollment(options);
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
   else items.forEach(job=>card(el,job,{...options,jobs,health}));
  }
 }
 async function start(candidate,{db,jobs,health,reload,showTab,toast}){
  if(!candidate||!candidate.id||!db){toast("Kirjaudu uudelleen ja valitse yritys.","error");return;}
  const active=(jobs||[]).find(j=>j.prospect_id===candidate.id&&isActive(j));
  // The owner can ALWAYS submit a private build request. A failed provider
  // health observation slows processing, not registration of the intent.
  // No paid model is enabled here; the GitHub worker checks credentials.
  if(active){
   // A repeated click must offer useful feedback and re-signal an eligible
   // existing job instead of silently doing nothing or creating duplicates.
   if(active.status==="queued"){
    const retryAt=Date.parse(active.next_eligible_at||"");
    if(Number.isFinite(retryAt)&&retryAt>Date.now()&&
       !["free_ai_rate_limit","free_ai_capacity_unavailable"].includes(active.error_code)){
     toast("Työ on tallessa. Seuraava sallittu yritys näkyy Demot-näkymässä.","error");
    }else{
     const result=await dispatchNow(db,active.id);
     dispatchFeedback(result,toast);
    }
   }else{
    toast("Yrityksen rakennustyö on jo käynnissä. Seuraa Demot-näkymää.","success");
   }
   showTab("demos");return;
  }
  try{
   const {data,error}=await db.rpc("kaurivo_request_demo_build",{p_prospect_id:candidate.id});
   if(error)throw error;
   if(!data)throw Error("Rakennustyön tunnistetta ei saatu.");
   // Trigger immediately with an authenticated owner session. Never put a
   // GitHub token in static HTML. Failed dispatch does NOT delete the job:
   // admin can retry or start GitHub manually.
   const dispatch=await dispatchNow(db,data);
   await reload();
   showTab("demos");
   dispatchFeedback(dispatch,toast);
  }catch(e){
   const message=String(e.message||"Tuntematon virhe");
   const human=message.includes("not authorized")?"Rakennuspyyntö vaatii Kaurivon ylläpitäjän kirjautumisen."
    :message.includes("company not found")?"Yritystä ei löydy yrityslistasta."
    :message;
   toast("Rakennustyötä ei käynnistetty: "+human,"error");
  }
 }
 window.KaurivoDemoJobs=Object.freeze({render,start,isActive,healthBlocked});
})();