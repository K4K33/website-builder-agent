/* Kaurivo internal CRM, dedicated Supabase Free project.
   Publishable client key ONLY. All records protected by PostgreSQL RLS.
   Never place a service-role key, customer invitation token or actual
   customer data into source control, static HTML, analytics or logs. */
(() => {
 "use strict";
 const SUPABASE_URL="https://xhsfbcwpwbgdbatrcyuk.supabase.co";
 const PUBLIC_KEY="sb_publishable_eESXBcqgycaQXzflfZN34w_nWP2ixvU";
 const ADMIN_EMAILS=new Set(["hello.kaurivo@gmail.com","kaarlo.kaukko1@gmail.com"]);
 const REVIEW_URL="https://k4k33.github.io/website-builder-agent/kaurivo/feedback/?lang=fi";
 const REDIRECT_URL="https://k4k33.github.io/website-builder-agent/kaurivo/admin/";
 const $=id=>document.getElementById(id);
 const helsinkiToday=()=>new Intl.DateTimeFormat("sv-SE",{timeZone:"Europe/Helsinki",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
 let selectedDay=new URLSearchParams(location.search).get("day")||helsinkiToday();
 if(!/^\d{4}-\d{2}-\d{2}$/.test(selectedDay))selectedDay=helsinkiToday();
 let db=null,activeTab="prospects",rows={clients:[],projects:[],sales:[],queue:[],reviews:[],invitations:[],prospects:[],events:[]};
 let currentInvite=null,busy=false;
 const label={lead:"Liidi",contacted:"Kontaktoitu",negotiating:"Neuvottelu",customer:"Asiakas",archived:"Arkistoitu",discovery:"Kartoitus",demo:"Demo",proposal:"Tarjous",building:"Rakenteilla",review:"Tarkistus",delivered:"Luovutettu",cancelled:"Peruttu",won:"Voitettu",lost:"Hävitty",pending:"Odottaa",prepared:"Valmisteltu",sent:"Lähetetty",urgent_review:"Kiireellinen",normal_review:"Normaali",clarify:"Tarkennettava",unverified:"Tarkistamatta",researching:"Tutkitaan",needs_demo:"Demoehdokas",ready_for_demo:"Valmis demoon",skipped:"Ohitettu",weak_evidence:"Selvä uudistustarpeen näyttö",
 adequate_evidence:"Sivu vaikuttaa toimivalta",none_confirmed:"Sivun puuttuminen tarkistettu",
 active_evidence:"Aktiivisuus havaittu",inactive_evidence:"Toiminta epävarmaa tai päättynyt",
 positive_evidence:"Myönteinen maksukyvyn viite",negative_evidence:"Heikko maksukyvyn viite",
 unknown:"Ei tietoa",unreviewed:"Tarkistamatta",strong:"Suuri tarve",moderate:"Kohtalainen tarve",
 weak:"Pieni tarve",not_started:"Ei aloitettu",brief_prepared:"Demobrief valmisteltu",
 reviewed:"Tarkistettu",not_reviewed:"Ei tarkistettu",
 needs_legal_review:"Laillisuustarkistus kesken",human_approved:"Ihminen hyväksynyt laillisuustarkistuksen",
 blocked:"Ei yhteydenottoa",not_contacted:"Ei kontaktoitu",drafted:"Luonnos",
 sent_manually:"Lähetetty käsin",responded:"Vastannut",opted_out:"Markkinointikielto"};
 const fmtDate=x=>x?new Date(x).toLocaleDateString("fi-FI",{day:"numeric",month:"numeric",year:"numeric",hour:"2-digit",minute:"2-digit"}):"Ei merkitty";
 const euro=x=>new Intl.NumberFormat("fi-FI",{style:"currency",currency:"EUR",maximumFractionDigits:0}).format(Number(x)||0);
 function toast(text,kind="info") {const el=$("status");el.textContent=text;el.className="status "+kind;el.hidden=false;window.clearTimeout(toast.timer);toast.timer=window.setTimeout(()=>el.hidden=true,7000);}
 function el(tag,cls,txt) {const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;}
 function append(parent,tag,cls,txt){const n=el(tag,cls,txt);parent.append(n);return n;}
 function button(txt,callback,cls="small-action"){const n=el("button",cls,txt);n.type="button";n.addEventListener("click",callback);return n;}
 function clientName(id){return rows.clients.find(x=>x.id===id)?.company_name||"Tuntematon yritys";}
 function projectName(id){return rows.projects.find(x=>x.id===id)?.project_name||"Ei projektia";}
 function stage(s){return label[s]||s||"—";}
 function record(container,title,sub,tag,kind){const card=append(container,"article","record");const main=append(card,"div","record-main");append(main,"div","record-title",title);append(main,"div","record-sub",sub);const actions=append(card,"div","record-actions");if(tag)append(actions,"span","tag "+(kind?"tag-"+kind:""),tag);return {card,main,actions};}
 function empty(target,text){append(target,"div","empty",text);}
 function closeMobileMore(restoreFocus=false){
  const panel=$("mobile-more-panel");
  if(!panel||panel.hidden)return;
  panel.hidden=true;
  $("mobile-more-button").setAttribute("aria-expanded","false");
  if(restoreFocus)$("mobile-more-button").focus();
 }
 function openMobileMore(){
  const panel=$("mobile-more-panel");
  if(!panel.hidden){closeMobileMore(true);return;}
  panel.hidden=false;
  $("mobile-more-button").setAttribute("aria-expanded","true");
  $("mobile-more-close").focus();
 }
 function showTab(tab){
  if(!["prospects","clients","projects","sales","queue","reviews"].includes(tab))return;
  activeTab=tab;
  for(const t of ["prospects","clients","projects","sales","queue","reviews"]){
   $("tab-"+t).hidden=t!==tab;
   const desktopButton=document.querySelector('[data-tab="'+t+'"]');
   desktopButton.classList.toggle("current",t===tab);
   desktopButton.setAttribute("aria-selected",t===tab?"true":"false");
   const mobileButton=document.querySelector('#mobile-dock [data-mobile-tab="'+t+'"]');
   if(mobileButton){
    mobileButton.classList.toggle("current",t===tab);
    if(t===tab)mobileButton.setAttribute("aria-current","page");
    else mobileButton.removeAttribute("aria-current");
   }
  }
  const more=$("mobile-more-button");
  if(more){
   const secondary=["sales","queue","reviews"].includes(tab);
   more.classList.toggle("current",secondary);
   if(secondary)more.setAttribute("aria-current","page");
   else more.removeAttribute("aria-current");
  }
  closeMobileMore();
 }
 function navigateMobile(tab){
  showTab(tab);
  if(window.matchMedia("(max-width: 850px)").matches){
   document.querySelector(".workspace").scrollIntoView({behavior:"smooth",block:"start"});
  }
 }
 
 // Evidence-based research priority, NOT a forecast of purchase or solvency.
 function leadEvidenceScore(c){
  // 0-100 research priority, not buying probability. Unreviewed/inactive
  // businesses never receive a verified recommendation score.
  if(!c.evidence_url || c.business_activity_assessment!=="active_evidence" ||
     c.customer_need==="unknown" || c.website_assessment==="unreviewed")return null;
  const need={strong:35,moderate:21,weak:8}[c.customer_need]||0; // 35
  const code=String(c.industry_code_hint||"");
  const priority=["41","42","43","45","47","49","55","56","69","71","73","74",
    "75","77","79","80","81","82","85","86","90","93","95","96",
    "6831","6832"].some(prefix=>code.startsWith(prefix))?25:12; // 25
  const activity=15; // active_evidence, human-confirmed
  const commercial={weak_evidence:15,none_confirmed:10,adequate_evidence:0}
    [c.website_assessment]||0; // 15
  const quality=c.language_evidence_url&&
    (c.website_found_url||c.website_listed_url)?10:5; // 10 evidence clarity
  return Math.min(100,need+priority+activity+commercial+quality);
 }
 function preliminaryScore(c){
  return Math.max(0,Math.min(60,Number(c.screening_priority)||0));
 }
 function leadReviewBand(c){
  const verified=leadEvidenceScore(c);
  if(verified!==null)return "Tutkittu · "+verified+"/100";
  const provisional=preliminaryScore(c);
  return provisional?
    "Alustava tutkimusjärjestys · "+provisional+"/60 (ei myyntiennuste)"
    :"Tutkimusprioriteetti: tiedot tarkistamatta";
 }
 function opsLabel(e){
  const kind={national_search:"Yöhaku",manual_search:"Varahaku",morning_push:"Aamuilmoitus"};
  const outcome={success:"Onnistui",failure:"Epäonnistui",skipped:"Ohitettu"};
  return (kind[e.component]||"Ajastus")+" · "+(outcome[e.outcome]||"Ei tietoa");
 }
 function renderOperations(){
  const events=rows.events||[];
  const panel=$("ops-events");panel.replaceChildren();
  const summary=$("ops-brief");
  const nightly=events.find(e=>e.component==="national_search");
  const manual=events.find(e=>e.component==="manual_search");
  const push=events.find(e=>e.component==="morning_push");
  const current=nightly||manual;
  const errors=[nightly,manual,push].filter(e=>e&&e.outcome==="failure");
  if(errors.length){
    summary.textContent="Häiriö havaittu · katso lisätiedot";
    $("ops-health").dataset.state="error";
  }else if(nightly?.outcome==="success"){
    summary.textContent="Yöhaku vahvistettu · "+nightly.records+" ehdokasta";
    $("ops-health").dataset.state="ok";
  }else if(manual?.outcome==="success"){
    summary.textContent="Varahaku vahvistettu · yöhaku tarkistamatta";
    $("ops-health").dataset.state="pending";
  }else{
    summary.textContent="Ei vielä vahvistettua yöajoa";
    $("ops-health").dataset.state="pending";
  }
  for(const component of ["national_search","manual_search","morning_push"]){
    const event=events.find(e=>e.component===component);
    const labels={national_search:"04.13 / PRH-yöhaku",
      manual_search:"Adminin manuaalinen haku",morning_push:"08.00 / aamuilmoitus"};
    const line=append(panel,"div","ops-event");
    append(line,"strong",null,labels[component]);
    append(line,"span",null,event
      ?opsLabel(event)+" · "+fmtDate(event.created_at)+
        (component==="morning_push"?" · "+event.notifications+" lähetetty":
         " · "+event.records+" yritystä")
      :"Ei vahvistettua tapahtumaa valitulle päivälle");
  }
  const reviewed=rows.prospects.filter(c=>c.review_status!=="unverified"&&c.review_status!=="skipped").length;
  const demos=rows.prospects.filter(c=>c.demo_stage!=="not_started").length;
  const links=rows.prospects.filter(c=>c.website_found_url||c.website_listed_url).length;
  const optouts=rows.prospects.filter(c=>c.marketing_opt_out).length;
  const sent=rows.prospects.filter(c=>["sent_manually","responded","won"].includes(c.outreach_stage)).length;
  const answered=rows.prospects.filter(c=>["responded","won"].includes(c.outreach_stage)).length;
  $("lead-pulse").textContent=
   reviewed+" / "+rows.prospects.filter(c=>c.review_status!=="skipped").length+
   " arvioitu · "+links+" sivulinkkiä · "+demos+" demobriefiä · "+
   sent+" kirjattua yhteydenottoa · "+answered+" vastausta · "+
   rows.sales.filter(c=>c.status==="won"&&c.source_verified).length+
   " vahvistettua kauppaa · "+optouts+" kieltoa (valitun päivän liidit, kaupat koko CRM)";
 }

 async function refreshSalesMetrics(){
  const status=$("sales-overview-status");
  const container=$("sales-overview-kpis"),bars=$("sales-overview-bars");
  if(!status||!container||!bars)return;
  try{
   if(!db||typeof db.rpc!=="function")throw Error("no_rpc");
   const {data,error}=await db.rpc("kaurivo_get_sales_dashboard");
   if(error||!data||typeof data!=="object"||Array.isArray(data))throw Error("missing_metrics");
   const keys=[
    ["discovered","Löydetty"],
    ["reviewed","Tutkittu"],
    ["site_links","Sivulinkki"],
    ["suggested_sites","Sivuehdotus"],
    ["demo_briefs","Demobrief"],
    ["legal_approved","Lakiarvio hyväksytty"],
    ["contacted","Käsin kontaktoitu"],
    ["responses","Vastannut"],
    ["wins","Vahvistettu kauppa"],
    ["opted_out","Markkinointikielto"]
   ];
   container.replaceChildren();
   for(const [key,title] of keys){
    const value=Number(data[key]);
    const item=append(container,"div","sales-kpi");
    append(item,"strong",null,Number.isFinite(value)?String(Math.max(0,value)):"—");
    append(item,"span",null,title);
   }
   const total=Number(data.won_eur);
   const totalBox=append(container,"div","sales-kpi sales-kpi-revenue");
   append(totalBox,"strong",null,Number.isFinite(total)?euro(total):"—");
   append(totalBox,"span",null,"Vahvistetun kaupan arvo");
   bars.replaceChildren();
   const daily=Array.isArray(data.daily)?data.daily:[];
   const clean=daily.filter(v=>v&&/^\d{4}-\d{2}-\d{2}$/.test(String(v.day))&&
      Number.isFinite(Number(v.new_leads))).slice(-14);
   if(clean.length){
    const max=Math.max(1,...clean.map(x=>Number(x.new_leads)));
    for(const day of clean){
     const bucket=append(bars,"div","sales-day");
     const bar=append(bucket,"div","sales-day-bar");
     bar.style.height=(Math.max(5,Math.round(Number(day.new_leads)/max*45)))+"px";
     bar.title=String(day.day)+": "+Number(day.new_leads)+" yritystä";
     append(bucket,"span",null,String(day.day).slice(5));
    }
   }else append(bars,"p","form-hint","Ei vielä päiväkohtaisia hakutuloksia viimeiseltä 30 päivältä.");
   status.textContent="Mittarit päivittyvät kaikista tallennetuista yrityksistä ja kaupoista.";
  }catch(_){
   // Never display guessed business totals if the verified database RPC fails.
   status.textContent="Koko myyntiputken lukemia ei voitu vahvistaa. Kokeile Päivitä tiedot.";
   container.replaceChildren();bars.replaceChildren();
  }
 }
 async function addSuppression(event){
  event.preventDefault();
  const b=$("add-suppression"),field=$("suppress-business-id"),note=$("suppression-note");
  if(b.disabled)return;
  const businessId=String(field.value||"").trim();
  if(!/^\d{7}-\d$/.test(businessId)){
   note.textContent="Tarkista Y-tunnuksen muoto: 1234567-8.";
   return;
  }
  if(!window.confirm("Vahvista yrityksen "+businessId+
     " markkinointikielto. Esto säilyy myös myöhemmissä PRH-hauissa. "+
     "Tämä ei lähetä mitään viestiä."))return;
  b.disabled=true;
  try{
   const {error}=await db.from("kaurivo_marketing_suppressions").insert({
    business_id:businessId,reason:"direct_marketing_objection"
   });
   if(error&&error.code!=="23505")throw error;
   field.value="";
   note.textContent="Yrityksen "+businessId+" markkinointikielto on tallennettu. "+
     "Kielto on voimassa myös seuraavissa hauissa.";
   toast("Markkinointikielto tallennettu turvalliseen estolistaan.","success");
   await reload();
  }catch(_){
   note.textContent="Kiellon tallennusta ei voitu vahvistaa. Kokeile uudelleen.";
   toast("Estolistan tallennus epäonnistui.","error");
  }finally{b.disabled=false;}
 }


 const languageNames={undetermined:"Ei tarkistettu",fi:"Suomi",sv:"Ruotsi",en:"Englanti",
   fi_sv:"Suomi ja ruotsi"};
 function swedishLanguageHint(c){
  const name=String(c.company_name||"");
  const place=String(c.city_hint||"").toUpperCase();
  return /\bAb\b|Bostads|Busstrafik|Restaurangdrift|Försäljning|Norrgård|Västra/i.test(name)||
   /JOMALA|MAARIANHAMINA|MARIEHAMN|ECKERÖ|LUMPARLAND|SOTTUNGA|ÅLAND/.test(place);
 }
 function companyHasMatchingObservation(c){
  if(!c.language_evidence_url)return false;
  const value=c.contact_language==="sv"?c.outreach_observation_sv:
    c.contact_language==="en"?c.outreach_observation_en:
    c.contact_language==="fi"?c.outreach_observation:"";
  return String(value||"").trim().length>=20;
 }
 function personalizedOutreachDraft(company){
  const language=String(company.contact_language||"undetermined");
  const observations={
   fi:String(company.outreach_observation||"").trim(),
   sv:String(company.outreach_observation_sv||"").trim(),
   en:String(company.outreach_observation_en||"").trim()
  };
  if(company.marketing_opt_out || company.outreach_review!=="human_approved" ||
     company.business_activity_assessment!=="active_evidence" ||
     !company.evidence_url || !company.language_evidence_url ||
     !["fi","sv","en"].includes(language) ||
     observations[language].length<20)
     throw Error("Viestin kieli, oma havainto, lähteet ja laillisuustarkistus on vahvistettava ensin.");
  const observation=observations[language];
  if(language==="sv")return [
    "Hej!",
    "",
    "Jag har tittat närmare på "+company.company_name+" och er webbplats. Jag lade märke till en konkret förbättringsmöjlighet: "+observation,
    "",
    "Jag heter Kaarlo och skriver från Kaurivo. Kaurivo är en modern webbstudio som skapar nya webbplatser och förnyar befintliga åt företag. Vi lägger vikt vid tydlig design, smidig mobilanvändning och innehåll som ni enkelt kan uppdatera själva.",
    "",
    "Jag skulle gärna visa en kort idé som utgår från er verksamhet och ert nuvarande varumärke. Skulle det vara intressant?",
    "",
    "Med vänliga hälsningar",
    "Kaarlo från Kaurivo",
    "",
    "Om ni inte vill få fler marknadsföringsmeddelanden från Kaurivo kan ni svara på detta mejl med: ingen mer kontakt."
   ].join("\n");
  if(language==="en")return [
    "Hello,",
    "",
    "I looked at "+company.company_name+"'s online presence and noticed a specific opportunity for improvement: "+observation,
    "",
    "I'm Kaarlo from Kaurivo. Kaurivo is a modern web design studio creating new websites and redesigning existing ones for businesses. We focus on distinctive design, a smooth mobile experience and content your team can easily update.",
    "",
    "I'd be happy to share a short concept based on your services and existing brand. Would that be of interest?",
    "",
    "Best regards",
    "Kaarlo from Kaurivo",
    "",
    "If you would prefer not to receive further marketing emails from Kaurivo, simply reply to this message with: no further contact."
   ].join("\n");
  return [
   "Hei,",
   "",
   "Tutustuin "+company.company_name+" -yrityksen verkkonäkyvyyteen ja huomasin yhden konkreettisen kehityskohdan: "+observation,
   "",
   "Olen Kaarlo Kaurivolta. Kaurivo on uuden sukupolven verkkosivustudio, joka rakentaa yrityksille uusia verkkosivuja ja uudistaa nykyisiä. Yhdistämme yrityksen näköisen suunnittelun, sujuvan mobiilikäytön ja sisällöt, joita yritys voi päivittää myös itse.",
   "",
   "Voisin valmistella teille lyhyen, yrityksenne palveluihin ja nykyiseen ilmeeseen sopivan uudistusehdotuksen. Olisiko tällaisesta hyötyä teille?",
   "",
   "Ystävällisin terveisin",
   "Kaarlo Kaurivolta",
   "",
   "Jos ette halua Kaurivolta uusia markkinointiyhteydenottoja, voitte vastata tähän viestiin: ei yhteydenottoja."
  ].join("\n");
 }
 function draftDemoBrief(c){
  const url=c.website_found_url||c.website_listed_url||c.website_candidate_url||"Ei vahvistettua URL-osoitetta";
  return [
   "KAURIVO · SISÄINEN DEMOBRIEF · EI JULKAISTU",
   "Yritys: "+c.company_name+" / "+c.business_id,
   "Alue: "+(c.city_hint||"vahvistettava"),
   "Toimialatieto (PRH): "+(c.industry_code_hint||"tuntematon"),
   "Nykyinen verkkosivuehdotus: "+url,
   "TARKISTETTU DEMON SIVUSTOKIELI: "+(languageNames[c.website_languages||"undetermined"]||"Tarkistettava"),
   "TARKISTETTU YHTEYDENOTTOKIELI: "+(languageNames[c.contact_language||"undetermined"]||"Tarkistettava"),
   "Kielen lähde: "+(c.language_evidence_url||"LISÄÄ KIELEN LÄHDE"),
   "Lähteet: "+(c.evidence_url||"LISÄÄ LÄHDE"),
   "",
   "1. VAHVISTA TOSIASIAT: yrityksen toiminta, palvelut, toimialan erityispiirteet, todellinen sivusto ja brändin oikeudet.",
   "2. KOLME VERTAILUKOHTAA: etsi 3 saman toimialan vahvaa sivustoa oikealla asiakaskielellä; dokumentoi navigaatio, ulkoasu ja luottamuselementit.",
   (c.website_languages==="sv"?
      "KIELIOHJE: toteuta koko asiakassivusto ja sisältö ruotsiksi (sv). Käytä luonnollista yrityksen toimialan sanastoa; älä julkaise suomenkielisiä paikkatekstejä.":
    c.website_languages==="fi_sv"?
      "KIELIOHJE: toteuta erilliset ruotsin- ja suomenkieliset sivut, näkyvä FI/SV-kielivalitsin, molemmilla kielillä koko navigaatio, lomakkeet, metatiedot ja omat URL:t.":
    c.website_languages==="en"?
      "KIELIOHJE: sivuston ensisijainen kieli on englanti; kaikki sivut, lomakkeet ja metatiedot vastaavat valittua kieltä.":
      "KIELIOHJE: toteuta sivusto suomeksi vasta asiakaskielen erillisen vahvistuksen jälkeen."),
   "3. EHDOTUS: kirkas arvolupaus, mobiilikäyttö, toimiva yhteydenottoreitti ja relevantein palvelurakenne.",
   "4. SISÄLTÖ: vain julkisesti todennetut yritysfaktat, ei keksittyjä arvosteluja tai palveluita.",
   "5. TOTEUTUS: premium-yksilöllinen sivusto, responsiivisuus, nopeus, esteettömyys sekä asiakkaan CMS-muokattavuus.",
   "6. QA: 320–1440 px, linkit, lomakkeet, liikkuvat elementit, tekstien todenperäisyys ja luvat.",
   "7. JULKAISU: EI automaattista asiakasdemon julkaisua tai yhteydenottoa ilman tarkistusta.",
   "",
   "Havaintoja: "+(c.research_notes||"Ei vielä havaintoja.")
  ].join("\n");
 }
 function prepareDemoBrief(c){
   if(!c.evidence_url||!["weak_evidence","none_confirmed"].includes(c.website_assessment)||
      c.business_activity_assessment!=="active_evidence"||c.customer_need==="unknown"||
      !c.language_evidence_url || !c.website_languages || c.website_languages==="undetermined"){
     toast("Vahvista ensin sivuston tarve, aktiivisuus, kielivalinta ja niiden lähteet ennen demobriefiä.","error");
     openEditor("prospect",c);return;
   }
   openEditor("prospect",c);
   $("field-demo_brief").value=c.demo_brief||draftDemoBrief(c);
   $("field-demo_stage").value="brief_prepared";
   toast("Demobrief-luonnos valmisteltu, tarkista ja tallenna. Ei ulkoisia AI-krediittejä.","success");
 }
 function render(){
  $("m-clients").textContent=rows.clients.length;
  $("m-projects").textContent=rows.projects.length;
  $("m-sales").textContent=rows.sales.filter(x=>x.status==="won"&&x.source_verified).length;
  $("m-feedback").textContent=rows.queue.filter(x=>x.status==="pending"||x.status==="prepared").length;
  const mobileCounts={
   clients:rows.clients.length,projects:rows.projects.length,
   sales:rows.sales.filter(x=>x.status==="won"&&x.source_verified).length,
   feedback:rows.queue.filter(x=>x.status==="pending"||x.status==="prepared").length
  };
  for(const [name,value] of Object.entries(mobileCounts)){
   const target=document.querySelector('[data-count="'+name+'"]');
   if(target)target.textContent=String(value);
  }
  $("now-label").textContent=new Date().toLocaleDateString("fi-FI",{day:"numeric",month:"long",year:"numeric"});
  renderOperations();
  const prospects=$("prospect-list");prospects.replaceChildren();
  $("prospect-day").value=selectedDay;
  const isToday=selectedDay===helsinkiToday();
  const excluded=rows.prospects.filter(x=>x.review_status==="skipped").length;
  let visible=rows.prospects.filter(x=>x.review_status!=="skipped"||
    $("show-skipped-prospects").checked).sort((a,b)=>{
     if(Boolean(a.marketing_opt_out)!==Boolean(b.marketing_opt_out))
      return Number(Boolean(a.marketing_opt_out))-Number(Boolean(b.marketing_opt_out));
     const aScore=leadEvidenceScore(a),bScore=leadEvidenceScore(b);
     if(aScore!==null&&bScore!==null)return bScore-aScore;
     if(aScore!==null)return -1;
     if(bScore!==null)return 1;
     const provisional=preliminaryScore(b)-preliminaryScore(a);
     if(provisional)return provisional;
     return Number(Boolean(b.website_found_url||b.website_listed_url||b.website_candidate_url))-
      Number(Boolean(a.website_found_url||a.website_listed_url||a.website_candidate_url));
    });
  const mode=$("lead-view").value;
  if(mode==="top")visible=visible.filter(x=>!x.marketing_opt_out&&
    x.screening_feedback!=="already_good_website"&&
    leadEvidenceScore(x)!==null&&leadEvidenceScore(x)>=65).slice(0,10);
  else if(mode==="research")visible=visible.filter(x=>!x.marketing_opt_out).slice(0,20);
  const withSites=visible.filter(x=>x.website_found_url||x.website_listed_url).length;
  const suggestions=visible.filter(x=>!x.website_found_url&&!x.website_listed_url&&x.website_candidate_url).length;
  $("morning-summary").textContent=rows.prospects.length
    ? visible.length+" yritystä tarkistettavana · "+withSites+" rekisteri-/tarkistuslinkkiä"+(suggestions?" · "+suggestions+" sivuehdotusta":"")+(excluded&&!$("show-skipped-prospects").checked
      ?" · "+excluded+" ohitettu":"")+" · "+selectedDay
    : isToday?"Tämän päivän lista ei ole vielä valmistunut. Tarkista yöajo.":"Ei listaa valitulta päivältä.";
  if(!visible.length)empty(prospects,mode==="top"
     ?"Ei vielä tarkistettuja, vähintään 65/100-pisteen myyntimahdollisuuksia. Tarkista ensin yritykset ja verkkosivut."
     :rows.prospects.length
      ?"Ei tässä näkymässä tarkistettavia yrityksiä. Voit näyttää myös ohitetut yritykset."
      :"Päivälle "+selectedDay+" ei löydy yrityksiä. Yöajo tai yritysten tuonti on voinut epäonnistua.");
  for(const candidate of visible){
   const row=record(prospects,candidate.company_name,
     (candidate.city_hint||"Kaupunki tuntematon")+" · Y-tunnus: "+candidate.business_id,
     stage(candidate.review_status));
   const verified=String(candidate.website_found_url||"");
   const listed=String(candidate.website_listed_url||"");
   const suggested=String(candidate.website_candidate_url||"");
   const website=verified||listed||suggested;
   if(website){
    try{
     const url=new URL(website);
     if(url.protocol==="https:"||url.protocol==="http:"){
      const link=append(row.main,"a","record-website",
       verified?"Avaa tallennettu verkkosivu ↗":listed?"Avaa PRH:n ilmoittama verkkosivu ↗":"Avaa mahdollinen verkkosivu ↗");
      link.href=url.href;link.target="_blank";link.rel="noopener noreferrer";
      append(row.main,"span","record-sub",url.hostname+" · "+
       (verified?"Tallennettu käsin · tarkista yrityksen vastaavuus":listed?"PRH:n ilmoittama · ei tarkistettu":"Hakukoneen ehdotus · EI vahvistettu, tarkista ennen tallennusta"));
     }
    }catch(_){append(row.main,"div","record-sub","Verkkosivulinkki on virheellinen · tarkista käsin");}
   }else{
    append(row.main,"div","record-no-website","PRH ei ilmoita verkkosivua · ei todista sivuttomuutta");
   }
   const findUrl=new URL("https://www.google.com/search");
   findUrl.searchParams.set("q",candidate.company_name+" yritys kotisivu "+candidate.business_id);
   const find=append(row.actions,"a","small-action prospect-search-site","Etsi verkkosivu ↗");
   find.href=findUrl.href;find.target="_blank";find.rel="noopener noreferrer";
   append(row.main,"div","record-sub","Toimiala: "+(candidate.industry_code_hint||"ei tietoa")+" · Lähde PRH/YTJ CC BY 4.0");
   if(candidate.research_notes)append(row.main,"div","record-note",candidate.research_notes);
   append(row.main,"div","record-sub","Yhteydenottokieli: "+
     (languageNames[candidate.contact_language||"undetermined"]||"Tarkistamatta")+
     " · Sivustokielet: "+
     (languageNames[candidate.website_languages||"undetermined"]||"Tarkistamatta"));
   if(candidate.contact_language==="undetermined"&&swedishLanguageHint(candidate))
    append(row.main,"div","record-warning",
      "Ruotsin kieli mahdollinen · tarkista yrityksen oma kieli ennen yhteydenottoa tai demoa. Nimi ja paikkakunta eivät yksin todista kieltä.");
   append(row.main,"div","record-sub",leadReviewBand(candidate));
   if(candidate.screening_reason)
    append(row.main,"div","record-sub","Hakuperusteet: "+String(candidate.screening_reason).slice(0,500));
   const audit=candidate.website_technical_audit||{};
   if(audit.status==="html_checked"){
    const problems=Array.isArray(audit.issues)?audit.issues:[];
    append(row.main,"div","record-sub",
      "Automaattinen HTML-tarkistus: "+problems.length+" mahdollista perustietojen puutetta"+
      " · "+(Number(audit.checked_internal_links)||0)+" sisälinkin pistotarkistusta"+
      " · "+(Number(audit.possible_broken_internal_links)||0)+" mahdollista HEAD-virhettä"+
      " · Ei Lighthouse-/visuaalinen arvio");
    if(audit.html_language_hint&&audit.html_language_hint!=="undetermined")
      append(row.main,"div","record-sub","Sivuston kielivihje: "+
       (languageNames[audit.html_language_hint]||"tuntematon")+
       " · tarkista ennen viestejä");
   }else if(audit.status&&audit.status!=="html_checked")
    append(row.main,"div","record-sub","Sivuston automaattinen tarkistus ei onnistunut ("+
      String(audit.status).slice(0,50)+")");
   if(candidate.screening_feedback&&candidate.screening_feedback!=="unrated")
    append(row.main,"div","record-sub","Oma asiakasarvio: "+({
     promising:"Lupaava",not_suitable:"Ei sopiva",
     already_good_website:"Nykyinen sivu jo hyvä",
     unresponsive:"Ei vastausta",client_won:"Asiakas saatu"
    }[candidate.screening_feedback]||"Merkitty"));
   if(candidate.marketing_opt_out)append(row.main,"div","record-warning","MARKKINOINTIKIELTO · ei yhteydenottoa");
   if(candidate.demo_stage!=="not_started")
    append(row.main,"div","record-sub","Demobrief: "+(candidate.demo_stage==="reviewed"?"tarkistettu":"valmisteltu, odottaa tarkistusta"));
   row.actions.append(button("Tarkista yritys",()=>openEditor("prospect",candidate)));
   if(candidate.demo_brief){
    row.actions.append(button("Kopioi demobrief",async()=>{
     try{
      await navigator.clipboard.writeText(candidate.demo_brief);
      toast("Demobrief kopioitu. Voit käyttää sitä sivuston suunnittelun lähtökohtana.","success");
     }catch(_){toast("Kopiointi ei onnistunut. Avaa yrityksen tiedot ja kopioi brief käsin.","error");}
    }));
   }
   if(candidate.review_status!=="skipped"&&!candidate.marketing_opt_out)
    row.actions.append(button("Valmistele demobrief",()=>prepareDemoBrief(candidate)));
   if(candidate.outreach_review==="human_approved" && !candidate.marketing_opt_out &&
      candidate.business_activity_assessment==="active_evidence" && companyHasMatchingObservation(candidate))
    row.actions.append(button("Kopioi tarkistettu viestiluonnos",async()=>{
     try{
      const draft=personalizedOutreachDraft(candidate);
      await navigator.clipboard.writeText(draft);
      toast("Yksilöllinen myyntiviestiluonnos kopioitu. Tarkista vastaanottaja, laki ja sisältö ennen manuaalista lähetystä.","success");
     }catch(err){
      toast(err.message||"Viestiluonnoksen kopiointi ei onnistunut.","error");
     }
    }));


  }
  const clients=$("client-list");clients.replaceChildren();
  if(!rows.clients.length)empty(clients,"Ei yrityksiä vielä. Aloita lisäämällä ensimmäinen.");
  for(const c of rows.clients){
   const r=record(clients,c.company_name,c.email+" · "+stage(c.status),stage(c.status));
   if(c.contact_name)append(r.main,"div","record-sub","Yhteyshenkilö: "+c.contact_name);
   if(c.website){const a=append(r.main,"a","record-sub",c.website);try{const u=new URL(c.website);if(["https:","http:"].includes(u.protocol))a.href=u.href;a.target="_blank";a.rel="noopener noreferrer";}catch(_){}}
   if(c.notes)append(r.main,"div","record-note",c.notes);
   r.actions.append(button("Muokkaa",()=>openEditor("client",c)));
  }
  const projects=$("project-list");projects.replaceChildren();
  if(!rows.projects.length)empty(projects,"Ei projekteja. Lisää asiakasyritys ja luo projekti.");
  for(const p of rows.projects){
   const r=record(projects,p.project_name,clientName(p.client_id)+" · "+stage(p.status),stage(p.status));
   if(p.editor_platform)append(r.main,"div","record-sub","Muokattavuus: "+p.editor_platform);
   if(p.must_haves)append(r.main,"div","record-note","Pakolliset toiveet: "+p.must_haves);
   if(p.demo_url)append(r.main,"div","record-sub","Demo: "+p.demo_url);
   r.actions.append(button("Muokkaa",()=>openEditor("project",p)));
  }
  const sales=$("sale-list");sales.replaceChildren();
  if(!rows.sales.length)empty(sales,"Ei kauppoja. Luo tarjous ja vahvista kauppa vasta toteutuneesta myynnistä.");
  for(const s of rows.sales){
   const r=record(sales,clientName(s.client_id),euro(s.amount_eur)+" · "+(s.project_id?projectName(s.project_id)+" · ":"")+stage(s.status),
    s.status==="won"&&s.source_verified?"Vahvistettu":stage(s.status),s.status==="won"&&s.source_verified?"won":null);
   if(s.confirmed_at)append(r.main,"div","record-sub","Kaupan päivä: "+fmtDate(s.confirmed_at));
   if(s.verification_note)append(r.main,"div","record-note","Vahvistuksen peruste: "+s.verification_note);
   if(s.status==="proposal")r.actions.append(button("Vahvista kauppa",()=>openConfirmSale(s)));
  }
  const queue=$("queue-list");queue.replaceChildren();
  if(!rows.queue.length)empty(queue,"Ei odottavia palautepyyntöjä. Vahvistetusta kaupasta muodostuu automaattisesti pyyntö yhden vuorokauden päähän.");
  for(const q of rows.queue){
   const sale=rows.sales.find(x=>x.id===q.sale_id);
   const r=record(queue,clientName(q.client_id),"Eräpäivä: "+fmtDate(q.due_at)+" · "+(sale?euro(sale.amount_eur):""),
     stage(q.status),q.status);
   const isDue=Date.now()>=new Date(q.due_at).getTime();
   if(q.status==="pending"){
    const b=button(isDue?"Valmistele palautekutsu":"Ei vielä erääntynyt",()=>prepareInvite(q));
    b.disabled=!isDue;r.actions.append(b);
   }else if(q.status==="prepared"){
    append(r.main,"div","record-sub","Kutsu on luotu. Alkuperäinen linkki näkyi vain luontihetkellä.");
    r.actions.append(button("Merkitse lähetetyksi",()=>markSent(q.id)));
   }else if(q.status==="sent")append(r.main,"div","record-sub","Lähetysaika: "+fmtDate(q.sent_at));
  }
  const reviews=$("review-list");reviews.replaceChildren();
  if(!rows.reviews.length)empty(reviews,"Ei palautteita. Oikeat arviot näkyvät täällä, kun asiakas lähettää lomakkeen.");
  for(const f of rows.reviews){
   const inv=rows.invitations.find(x=>x.id===f.invitation_id);
   const r=record(reviews,(Number(f.rating)||0)+" / 5 ★ · "+(inv?.verified_company||"Palaute"),fmtDate(f.submitted_at)+" · "+(f.topic||"yleinen"),stage(f.priority),f.priority==="urgent_review"?"urgent":null);
   append(r.main,"div","record-note",f.comment_text||"");
   append(r.main,"div","record-sub",f.source_verified?"Vahvistettu lähde":"Lähde vahvistettava erikseen");
  }
 }
 async function reload(){
  if(!db||busy)return;
  busy=true;
  try{
   const entities=[
    ["prospects","kaurivo_crm_prospects"],["events","kaurivo_pipeline_events"],["clients","kaurivo_crm_clients"],["projects","kaurivo_crm_projects"],
    ["sales","kaurivo_crm_sales"],["queue","kaurivo_crm_feedback_queue"],
    ["reviews","kaurivo_feedback_submissions"],["invitations","kaurivo_feedback_invitations"]
   ];
   const results=await Promise.all(entities.map(([key,table])=>{
    let query=db.from(table).select("*");
    if(key==="prospects")return query.eq("discovery_date",selectedDay).order("created_at",{ascending:false}).limit(100);
    if(key==="events")return query.eq("event_day",selectedDay).order("created_at",{ascending:false}).limit(30);
    return query.order(key==="reviews"?"submitted_at":"created_at",{ascending:false}).limit(250);
   }));
   for(let i=0;i<results.length;i++){
    const {data,error}=results[i];if(error)throw error;rows[entities[i][0]]=data||[];
   }
   render();
   await refreshSalesMetrics();
  }catch(err){toast("Tietojen lataus epäonnistui. Tarkista käyttöoikeudet: "+(err.message||"tuntematon virhe"),"error");}
  finally{busy=false;}
 }
 const forms={
  prospect:{title:"Yrityksen taustatutkimus",table:"kaurivo_crm_prospects",fields:[
   ["review_status","Tutkimuksen vaihe","choice",true,["unverified","researching","needs_demo","ready_for_demo","skipped"]],
   ["screening_feedback","Asiakasvalinnan palaute (vain tarkistettu tieto)","choice",true,["unrated","promising","not_suitable","already_good_website","unresponsive","client_won"]],
   ["website_found_url","Oikea verkkosivu (itse tarkistettu, https://...)","url"],
   ["website_assessment","Verkkosivun arvio","choice",true,["unreviewed","weak_evidence","adequate_evidence","none_confirmed"]],
   ["business_activity_assessment","Yrityksen aktiivisuuden näyttö","choice",true,["unreviewed","active_evidence","inactive_evidence"]],
   ["payment_signal","Maksukyvyn havainto (ei ennuste)","choice",true,["unknown","positive_evidence","negative_evidence"]],
   ["customer_need","Verkkosivu-uudistuksen tarve","choice",true,["unknown","strong","moderate","weak"]],
   ["evidence_url","Havaintojen julkinen lähdelinkki (https://...)","url"],
   ["demo_stage","Demobriefin vaihe","choice",true,["not_started","brief_prepared","reviewed"]],
   ["demo_brief","Sisäinen demobrief ja QA-ohje","textarea"],
   ["contact_language","Yhteydenottokieli (tarkista yrityksen omista tiedoista)","choice",true,["undetermined","fi","sv","en"]],
   ["website_languages","Demon sivustokielet","choice",true,["undetermined","fi","sv","fi_sv","en"]],
   ["language_evidence_url","Kielen lähde (yrityksen sivu tai rekisteritieto, HTTPS)","url"],
   ["outreach_observation","Yksilöllinen havainto SUOMEKSI","textarea"],
   ["outreach_observation_sv","Yksilöllinen havainto RUOTSIKSI (ruotsinkieliseen viestiin)","textarea"],
   ["outreach_observation_en","Yksilöllinen havainto ENGLANNIKSI","textarea"],
   ["outreach_review","Yhteydenoton lainmukaisuuden tarkistus","choice",true,["not_reviewed","needs_legal_review","human_approved","blocked"]],
   ["outreach_stage","Yhteydenoton vaihe (ei lähetä viestejä)","choice",true,["not_contacted","drafted","sent_manually","responded","won","opted_out"]],
   ["marketing_opt_out","Yritys on kieltänyt markkinoinnin","checkbox"],
   ["research_notes","Vahvistetut faktat, puutteet ja lähteet","textarea"]]},
  client:{title:"Yrityksen tiedot",table:"kaurivo_crm_clients",fields:[
   ["company_name","Yrityksen nimi","text",true],["contact_name","Yhteyshenkilö","text"],
   ["email","Sähköposti","email",true],["website","Verkkosivu (https://...)","url"],
   ["status","Tila","choice",true,["lead","contacted","negotiating","customer","archived"]],
   ["notes","Muistiinpanot","textarea"]]},
  project:{title:"Verkkosivuprojekti",table:"kaurivo_crm_projects",fields:[
   ["client_id","Yritys","clients",true],["project_name","Projektin nimi","text",true],
   ["status","Vaihe","choice",true,["discovery","demo","proposal","building","review","delivered","cancelled"]],
   ["demo_url","Demon osoite","url"],["delivered_url","Valmis verkkosivu","url"],
   ["editor_platform","Asiakkaan muokkaustyökalu","text"],
   ["must_haves","Mitä asiakkaan sivulla pitää ehdottomasti olla?","textarea"],
   ["due_date","Tavoitepäivä","date"]]},
  sale:{title:"Uusi tarjous",table:"kaurivo_crm_sales",fields:[
   ["client_id","Yritys","clients",true],["project_id","Liittyvä projekti","projects"],
   ["amount_eur","Tarjous / €","number",true]]}
 };
 let editing=null;
 function inputField(def,value,context){
  const [name,title,type,required,options]=def;
  const wrapper=el("div","field"),labelEl=append(wrapper,"label",null,title);
  let control;
  if(type==="textarea")control=el("textarea");
  else if(type==="checkbox"){control=el("input");control.type="checkbox";control.checked=Boolean(value);}
  else if(type==="choice"||type==="clients"||type==="projects"){
   control=el("select");const vals=type==="choice"?options.map(v=>[v,stage(v)]):
    type==="clients"?rows.clients.map(v=>[v.id,v.company_name]):
    [["","Ei projektia"],...rows.projects.filter(p=>!context?.client_id||p.client_id===context.client_id).map(v=>[v.id,v.project_name])];
   if(type==="projects")vals[0]=["","Ei projektia"];
   for(const pair of vals){const option=el("option",null,pair[1]);option.value=pair[0];control.append(option);}
  }else{control=el("input");control.type=type;}
  control.id="field-"+name;control.name=name;
  labelEl.htmlFor=control.id;control.required=Boolean(required);
  if(type==="number"){control.step=".01";control.min="0";}
  if(type==="textarea")control.maxLength=5000;
  if(type!=="checkbox"&&value!==undefined&&value!==null)control.value=String(value);
  wrapper.append(control);return wrapper;
 }
 function openEditor(kind,recordValue){
  if(kind==="project"&&!rows.clients.length||kind==="sale"&&!rows.clients.length){toast("Lisää yritys ensin.");return;}
  editing={kind,record:recordValue||null};
  const spec=forms[kind];$("editor-heading").textContent=spec.title;
  const box=$("editor-fields");box.replaceChildren();
  const defs=spec.fields;
  for(const d of defs)box.append(inputField(d,recordValue?.[d[0]],recordValue));
  if(kind==="sale")append(box,"p","field-hint","Tarjous kirjataan aluksi avoimeksi. Kaupan vahvistaminen tehdään vasta, kun toteutunut myynti on todennettu.");
  $("editor").showModal();
 }
 async function saveEditor(event){
  event.preventDefault();if(!editing||busy)return;
  const {kind,record:old}=editing;
  const spec=forms[kind],data={};
  for(const [key,,type,required] of spec.fields){
   const value=type==="checkbox"?$("field-"+key).checked:$("field-"+key).value.trim();
   if(required&&!value){toast("Täytä pakolliset kentät.","error");return;}
   data[key]=type==="checkbox"?value:type==="number"?Number(value):(value||null);
  }
  if(kind==="prospect"){
   data.research_notes=data.research_notes||"";
   data.outreach_observation=data.outreach_observation||"";
   data.outreach_observation_sv=data.outreach_observation_sv||"";
   data.outreach_observation_en=data.outreach_observation_en||"";
   data.language_evidence_url=data.language_evidence_url||"";
   if([data.outreach_observation,data.outreach_observation_sv,data.outreach_observation_en].some(v=>v.length>600)){
    toast("Yksilöllinen havainto saa olla enintään 600 merkkiä per kieli.","error");return;
   }
   if(data.language_evidence_url){
    try{const u=new URL(data.language_evidence_url);
     if(u.protocol!=="https:"||u.username||u.password||data.language_evidence_url.length>1200)
      throw Error("invalid");
    }catch(_){toast("Kielen lähteen pitää olla kelvollinen HTTPS-linkki.","error");return;}
   }
   data.website_found_url=data.website_found_url||"";
   if(data.website_found_url){
    let u;
    try{u=new URL(data.website_found_url);}catch(_){toast("Tarkista verkkosivun osoite.","error");return;}
    if(!["http:","https:"].includes(u.protocol)||u.username||u.password||
       data.website_found_url.length>1200){
     toast("Verkkosivun osoitteen on oltava kelvollinen HTTP(S)-osoite.","error");return;
    }
   }
   data.demo_brief=data.demo_brief||"";
   data.evidence_url=data.evidence_url||"";
   if(data.evidence_url){
    try{
     const u=new URL(data.evidence_url);
     if(u.protocol!=="https:"||u.username||u.password||data.evidence_url.length>1200)
      throw Error("invalid");
    }catch(_){toast("Havaintojen lähteen on oltava kelvollinen HTTPS-linkki.","error");return;}
   }
   const observed=[data.website_assessment!=="unreviewed",
     data.business_activity_assessment!=="unreviewed",
     data.payment_signal!=="unknown",data.customer_need!=="unknown"];
   if(observed.some(Boolean)&&!data.evidence_url){
    toast("Täytä lähdelinkki, kun vahvistat yrityksen arviointitietoja.","error");return;
   }
   if(["promising","not_suitable","already_good_website"].includes(data.screening_feedback)&&
      (!data.evidence_url||data.review_status==="unverified")){
    toast("Kirjaa palautteen perusteeksi tutkimuksen lähde ja tarkistettu vaihe.","error");return;
   }
   if(data.screening_feedback==="already_good_website"&&
      data.website_assessment!=="adequate_evidence"){
    toast("Hyvä verkkosivu -palaute edellyttää erikseen tarkistettua sivustoa.","error");return;
   }
   if(data.screening_feedback==="client_won"&&data.outreach_stage!=="won"){
    toast("Asiakkaaksi saaminen edellyttää vahvistettua kaupan tilaa.","error");return;
   }
   if(data.screening_feedback==="unresponsive"&&data.outreach_stage!=="sent_manually"){
    toast("Ei vastausta -merkintä vaatii ensin laillisen, käsin lähetetyn viestin.","error");return;
   }
   if(data.demo_stage!=="not_started"&&(
      !data.language_evidence_url||data.website_languages==="undetermined")){
    toast("Tarkista demon sivustokielet ja merkitse kielen lähde.","error");return;
   }
   if(data.demo_stage!=="not_started"&&!data.demo_brief.trim()){
    toast("Kirjoita demobrief ennen valmisteluvaiheen tallentamista.","error");return;
   }
   if(data.marketing_opt_out||old?.marketing_opt_out){
    data.marketing_opt_out=true;
    data.outreach_review="blocked";
    data.outreach_stage="opted_out";
   }
   if(["sent_manually","responded","won"].includes(data.outreach_stage)&&
      data.outreach_review!=="human_approved"){
     toast("Yhteydenottoa ei voi kirjata lähetetyksi tai vastatuksi ennen erillistä laillisuushyväksyntää.","error");return;
   }
   if(data.outreach_stage==="opted_out"&&!data.marketing_opt_out){
    toast("Merkitse markkinointikielto ennen luopumistilan tallennusta.","error");return;
   }
   if(data.outreach_review==="human_approved"&&!data.marketing_opt_out){
    if(data.business_activity_assessment!=="active_evidence"||!data.evidence_url||
      data.customer_need==="unknown"||data.contact_language==="undetermined"||
      !data.language_evidence_url||!companyHasMatchingObservation(data)){
     toast("Yhteydenotto vaatii tarkistetun kielen, oman kielisen havainnon, aktiivisuuden, tarpeen ja lähteet.","error");return;
    }
    if(!window.confirm("Vahvistatko, että vastaanottajatyyppi, soveltuva B2B-suoramarkkinoinnin laki, GDPR-tiedot, estolistat ja maksuton kielto-ohje on tarkistettu erikseen? Tämä EI lähetä viestiä."))return;
   }
   // Website URLs and registry facts never automatically prove identity or payment capacity.
   data.website_verified=false;
  }
  if(kind==="sale"){data.status="proposal";data.source_verified=false;data.confirmed_at=null;}
  if(kind==="client"){data.contact_name=data.contact_name||"";data.website=data.website||"";data.notes=data.notes||"";}
  if(kind==="project"){data.demo_url=data.demo_url||"";data.delivered_url=data.delivered_url||"";data.must_haves=data.must_haves||"";data.editor_platform=data.editor_platform||"";}
  try{
   const query=db.from(spec.table);
   const res=old?await query.update(data).eq("id",old.id).select("id"):await query.insert(data).select("id");
   if(res.error)throw res.error;
   if(!res.data?.length)throw new Error("Tietoa ei tallennettu tai käyttöoikeus puuttuu.");
   $("editor").close();editing=null;toast("Tiedot tallennettu.","success");await reload();
  }catch(err){toast("Tallennus epäonnistui: "+(err.message||"Tuntematon"),"error");}
 }
 function openConfirmSale(s){
  editing={kind:"verify_sale",record:s};
  $("editor-heading").textContent="Vahvista toteutunut kauppa";
  const box=$("editor-fields");box.replaceChildren();
  append(box,"p","form-hint","Vahvista vain kauppa, joka on oikeasti sovittu tai maksettu. Tämä käynnistää seuraavan päivän palautepyyntöjonon.");
  box.append(inputField(["verification_note","Mihin vahvistus perustuu? (vähintään 5 merkkiä)","textarea",true],""));
  const amount=append(box,"p","form-hint",clientName(s.client_id)+" · "+euro(s.amount_eur));
  $("editor").showModal();
 }
 async function confirmSale(event){
  event.preventDefault();const s=editing?.record;const note=$("field-verification_note")?.value.trim()||"";
  if(!s||note.length<5){toast("Kirjoita kaupan todellinen vahvistusperuste.","error");return;}
  try{
   const result=await db.from("kaurivo_crm_sales").update({
     status:"won",source_verified:true,verification_note:note,confirmed_at:new Date().toISOString()
   }).eq("id",s.id).eq("status","proposal").select("id");
   if(result.error)throw result.error;
   if(!result.data?.length)throw new Error("Kauppaa ei enää löytynyt avoimena.");
   $("editor").close();editing=null;
   toast("Kauppa vahvistettu. Palautepyyntö lisätty jonoon huomiselle.","success");await reload();showTab("queue");
  }catch(err){toast("Kaupan vahvistus epäonnistui: "+(err.message||""),"error");}
 }
 function secureToken(){
  const bytes=new Uint8Array(32);crypto.getRandomValues(bytes);
  let binary="";for(const b of bytes)binary+=String.fromCharCode(b);
  return btoa(binary).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
 }
 async function sha256(text){const bytes=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(text));return Array.from(new Uint8Array(bytes)).map(v=>v.toString(16).padStart(2,"0")).join("");}
 async function prepareInvite(q){
  if(busy)return;
  if(q.status!=="pending"||Date.now()<new Date(q.due_at).getTime()){toast("Kutsu ei ole vielä erääntynyt.","error");return;}
  const sale=rows.sales.find(s=>s.id===q.sale_id),client=rows.clients.find(c=>c.id===q.client_id);
  if(!sale||!client||sale.status!=="won"||!sale.source_verified){toast("Vahvistettua kauppaa ei löytynyt.","error");return;}
  busy=true;
  try{
   const token=secureToken(),hash=await sha256(token);
   const res=await db.rpc("kaurivo_prepare_feedback_invitation",{p_sale_id:sale.id,p_token_sha256:hash});
   if(res.error)throw res.error;if(res.data!==true)throw new Error("Kutsu ei ole valmis tai se on jo luotu.");
   const link=REVIEW_URL+"#invite="+token;
   const message="Hei!\n\nKiitos luottamuksesta Kaurivoon! Haluamme kuulla, miten tarjous, yhteydenpito ja yhteistyön aloittaminen sujuivat. Voit antaa 1–5 tähteä ja lyhyen palautteen turvallisella lomakkeella:\n\n"+link+"\n\nPalaute pysyy yksityisenä eikä sitä julkaista ilman erillistä lupaa.\n\nKaurivo\nAsiakaskokemus";
   currentInvite={sale_id:sale.id,queue_id:q.id,email:client.email,message};
   $("invite-copy").value="Vastaanottaja: "+client.email+"\nAihe: Kaurivo | Miten asiointi sujui?\n\n"+message;
   $("invite-dialog").showModal();
   toast("Yksilöllinen palautekutsu on luotu. Kopioi se ennen sulkemista.","success");
  }catch(err){toast("Kutsun valmistelu epäonnistui: "+(err.message||""),"error");}
  finally{busy=false;await reload();}
 }
 async function copyInvite(){
  if(!currentInvite)return;
  try{await navigator.clipboard.writeText($("invite-copy").value);toast("Viesti kopioitu. Lähetä se oikealle asiakkaalle Kaurivon Gmailista.","success");}
  catch(_){$("invite-copy").select();toast("Valitse ja kopioi viesti käsin.","error");}
 }
 async function markSent(queueId){
  const id=queueId||currentInvite?.queue_id;
  if(!id)return;
  if(!window.confirm("Vahvistatko, että olet jo lähettänyt henkilökohtaisen palautekutsun Kaurivon Gmailista oikealle asiakkaalle?"))return;
  const res=await db.from("kaurivo_crm_feedback_queue").update({status:"sent",sent_at:new Date().toISOString()}).eq("id",id).eq("status","prepared").select("id");
  if(res.error||!res.data?.length){toast("Lähetetyksi merkitseminen epäonnistui.","error");return;}
  currentInvite=null;$("invite-copy").value="";$("invite-dialog").close();
  toast("Pyyntö kirjattiin lähetetyksi.","success");await reload();
 }

 async function importProspects(file){
  if(file.size>3000000){toast("Tiedosto on liian suuri (enintään 3 Mt).","error");return;}
  let packet;
  try{packet=JSON.parse(await file.text());}
  catch(_){toast("Tiedosto ei ole kelvollinen JSON.","error");return;}
  if(packet.schema!=="kaurivo_prh_shortlist_v1"||packet.mode!=="pilot-live"||
     !packet.review_required||packet.not_verified_for_outreach!==true||
     !Array.isArray(packet.candidates)||packet.candidates.length>50||
     packet.candidates.length<1||!/^\\d{4}-\\d{2}-\\d{2}$/.test(packet.date||"")){
   toast("Valitse oikean PRH-yöajon crm-shortlist.json, ei demoa tai testaustiedostoa.","error");return;
  }
  const today=new Date();const d=new Date(packet.date+"T00:00:00Z");
  if(!Number.isFinite(d.getTime())||Math.abs(today.getTime()-d.getTime())>32*86400000){
   toast("Liidilista on vanhentunut. Käytä enintään 30 päivän takaista ajoa.","error");return;
  }
  const clean=s=>String(s||"").replace(/[\\u0000-\\u001f\\u007f]/g," ").trim();
  const validUrl=v=>{try{const u=new URL(v);return u.protocol==="https:"&&!!u.hostname&&!u.username&&!u.password;}catch(_){return false;}};
  const items=[],seen=new Set();
  for(const c of packet.candidates){
   if(!c||!/^prh:[0-9]{7}-[0-9]$/.test(c.identity||"")||!(/^[0-9]{7}-[0-9]$/).test(c.business_id||"")||
      c.identity!=="prh:"+c.business_id||typeof c.name!=="string"||c.name.trim().length<2||
      c.website_absence_verified!==false||c.business_activity!=="unverified"||
      c.outreach_authorized!==false||c.demo_authorized!==false){
    toast("Liidilistassa on puuttuvia tai epäluotettavia tietoja. Tuonti keskeytettiin.","error");return;
   }
   if(seen.has(c.business_id))continue;seen.add(c.business_id);
   const url=clean(c.website_listed_url);
   if(url&&!validUrl(url)){toast("PRH-verkkosivulinkki ei ole kelvollinen.","error");return;}
   const suggestion=c.website_search_candidate;
   const proposed=typeof suggestion==="object"&&suggestion!==null &&
      suggestion.source==="tavily_search" && Number.isInteger(suggestion.confidence) &&
      suggestion.confidence>=80 && suggestion.confidence<=99 &&
      typeof suggestion.url==="string" && validUrl(suggestion.url) ?
      clean(suggestion.url).slice(0,1200):"";
   items.push({
    website_candidate_url:proposed,
    website_candidate_source:proposed?"tavily_search":"",
    website_candidate_confidence:proposed?suggestion.confidence:0,
    website_candidate_checked_at:proposed?new Date().toISOString():null,
    business_id:c.business_id,company_name:clean(c.name).slice(0,160),
    city_hint:clean(c.city_hint).slice(0,80),
    industry_code_hint:clean(c.industry_code_hint).slice(0,20),
    website_listed_url:url.slice(0,1200),
    source_url:"https://avoindata.prh.fi/",
    source_kind:"prh_registry",discovery_date:packet.date,review_status:"unverified",
    activity_verified:false,website_verified:false,financial_verified:false
   });
  }
  if(!window.confirm("Tuodaanko "+items.length+" julkisen PRH-yritysrekisterin liidiä YKSITYISEEN tarkistusjonoon? Tuonti ei lähetä viestejä."))return;
  try{
   const {error}=await db.from("kaurivo_crm_prospects").upsert(items,{onConflict:"business_id",ignoreDuplicates:true});
   if(error)throw error;
   toast("Liidit tuotu tarkistettavaksi. Jo olemassa olevia yrityksiä ei muutettu.","success");
   await reload();showTab("prospects");
  }catch(err){toast("Liidien tuonti epäonnistui: "+(err.message||""),"error");}
 }

 const MANUAL_SCAN_URL=SUPABASE_URL+"/functions/v1/kaurivo-manual-scan";
 async function startManualScan(){
  const b=$("start-manual-scan");
  if(b.disabled)return;
  const status=$("manual-scan-status");
  const email=(await db.auth.getUser()).data?.user?.email?.toLowerCase();
  if(!ADMIN_EMAILS.has(email)){toast("Kirjaudu ylläpitotilille ennen yrityshakua.","error");return;}
  b.disabled=true;
  b.textContent="Haetaan yrityksiä…";
  status.textContent="Haetaan yrityksiä PRH:sta. Älä sulje sovellusta ennen hakutulosta.";
  try{
   const {data:{session}}=await db.auth.getSession();
   if(!session?.access_token)throw Error("Istunto päättyi, kirjaudu uudelleen.");
   const response=await fetch(MANUAL_SCAN_URL,{
    method:"POST",headers:{"Content-Type":"application/json",
     "apikey":PUBLIC_KEY,"Authorization":"Bearer "+session.access_token},
    body:JSON.stringify({action:"scan"})
   });
   const result=await response.json().catch(()=>({}));
   if(response.status===429||result.reason==="cooldown_or_daily_limit"){
    status.textContent="Varahaun raja tuli vastaan. Enintään 3 käynnistystä päivässä, vähintään 25 min välein.";
    toast("Varahaku on tilapäisesti rajoitettu. Yöajo toimii erikseen.","error");
    return;
   }
   if(!response.ok||!result.ok){
    status.textContent="Varahaku epäonnistui. PRH:n rajapinta tai tallennus ei vastannut. Päivän yrityslistaa ei keksitä.";
    throw Error("PRH-haku ei onnistunut. Tarkista myöhemmin tai odota yöajoa.");
   }
   const count=Number(result.added)||0;
   const examined=Number(result.examined)||0;
   status.textContent="Haku valmis. "+examined+" PRH-tietuetta tarkasteltu, "+
    count+" uutta yritystä lisätty. Tiedot ovat tarkistamattomia.";
   selectedDay=helsinkiToday();
   await reload();
   showTab("prospects");
   toast(count>0?count+" yritystä lisätty päivän listalle.":"Haku valmis: ei uusia yrityksiä tällä kierroksella.","success");
  }catch(err){toast("Yrityshaun virhe: "+(err.message||"Tuntematon virhe"),"error");}
  finally{b.disabled=false;b.textContent="Käynnistä yrityshaku";}
 }
 const PUSH_URL=SUPABASE_URL+"/functions/v1/kaurivo-daily-push";
 const isStandalone=()=>window.matchMedia("(display-mode: standalone)").matches||window.navigator.standalone===true;
 function toUint8(base64url){
  const str=atob(base64url.replace(/-/g,"+").replace(/_/g,"/").padEnd(Math.ceil(base64url.length/4)*4,"="));
  return Uint8Array.from(str,ch=>ch.charCodeAt(0));
 }
 async function pushRequest(method,body){
  const {data:{session}}=await db.auth.getSession();
  if(!session?.access_token)throw Error("Kirjaudu sisään ensin.");
  const result=await fetch(PUSH_URL,{
   method,headers:{"Content-Type":"application/json","apikey":PUBLIC_KEY,
    "Authorization":"Bearer "+session.access_token},
   ...(body?{body:JSON.stringify(body)}:{})
  });
  const data=await result.json().catch(()=>({}));
  if(!result.ok||data.ok===false)throw Error("Ilmoituspalvelu ei vastannut ("+result.status+").");
  return data;
 }
 async function syncPushStatus(){
  const status=$("push-status"),test=$("test-push");
  if(!status||!test)return;
  if(!("serviceWorker" in navigator)||!("PushManager" in window)||!("Notification" in window)){
   status.textContent="iPhonessa: lisää ensin Safari-sivu aloitusnäytölle ja avaa sovelluksena.";
   test.hidden=true;return;
  }
  try{
   const reg=await navigator.serviceWorker.register("./sw.js",{scope:"./"});
   const sub=await reg.pushManager.getSubscription();
   const permitted=Notification.permission==="granted";
   let registered=false,deviceCount=0;
   if(sub&&permitted){
    // If permission was granted previously, repair a missing server-side
    // subscription without triggering another iOS permission prompt.
    try{
     const res=await pushRequest("POST",{action:"subscribe",subscription:sub.toJSON()});
     registered=Boolean(res.subscribed);
    }catch(_){}
   }
   try{
    const server=await pushRequest("GET");
    deviceCount=Number(server.registeredDevices)||0;
    registered=registered||Boolean(sub&&permitted&&deviceCount>0);
   }catch(_){registered=false;}
   if(permitted&&registered){
    status.textContent="Push-tilaus vahvistettu palvelimella · "+
       deviceCount+" laitetta. Voit tehdä testi-ilmoituksen.";
   }else if(permitted){
    status.textContent="iPhonen ilmoituslupa sallittu, mutta palvelimella ei ole vahvistettua tilausta. Paina Salli ilmoitukset.";
   }else{
    status.textContent="Ilmoitustilaus ei ole aktiivinen tässä sovelluksessa.";
   }
   test.hidden=!registered;
   $("enable-push").textContent=registered?"Päivitä tila":"Salli ilmoitukset";
  }catch(_){status.textContent="Ilmoitustilan tarkistus ei onnistunut.";test.hidden=true;}
 }
 async function enablePush(){
  const btn=$("enable-push");btn.disabled=true;
  try{
   if(!("Notification" in window)||!("PushManager" in window)||!("serviceWorker" in navigator))
    throw Error("Avaa Kaurivo aloitusnäytölle lisättynä sovelluksena, ei tavallisessa Safari-välilehdessä.");
   // The permission prompt is initiated from the admin's explicit tap.
   const permission=await Notification.requestPermission();
   if(permission!=="granted")throw Error("Ilmoitukset on estetty. Muuta lupa iPhonen asetuksissa.");
   const reg=await navigator.serviceWorker.register("./sw.js",{scope:"./"});
   const key=await pushRequest("GET");
   let sub=await reg.pushManager.getSubscription();
   if(!sub)sub=await reg.pushManager.subscribe({
    userVisibleOnly:true,applicationServerKey:toUint8(key.publicKey)
   });
   const data=await pushRequest("POST",{action:"subscribe",subscription:sub.toJSON()});
   if(!data.subscribed)throw Error("Ilmoitustilausta ei voitu vahvistaa.");
   toast("Ilmoitukset otettu käyttöön. Saat viestin, kun aamun lista on valmis.","success");
  }catch(err){toast(err.message||"Ilmoituksia ei voitu sallia.","error");}
  finally{btn.disabled=false;await syncPushStatus();}
 }
 async function testPush(){
  const btn=$("test-push");btn.disabled=true;
  try{
   const result=await pushRequest("POST",{action:"test"});
   if(!result.sent)throw Error("Testi-ilmoitus ei lähtenyt yhdellekään laitteelle.");
   toast("Testi-ilmoitus lähetetty ("+result.sent+" laitetta).","success");
  }catch(err){toast(err.message||"Testi epäonnistui.","error");}
  finally{btn.disabled=false;}
 }
 async function unsubscribePush(){
  try{
   if(!("serviceWorker" in navigator))return;
   const reg=await navigator.serviceWorker.getRegistration("./");
   const sub=await reg?.pushManager?.getSubscription();
   if(sub){
    await pushRequest("POST",{action:"unsubscribe",endpoint:sub.endpoint});
    await sub.unsubscribe();
   }
  }catch(_){ /* User can still revoke notifications via device settings. */ }
 }

 function setLogin(isAuthenticated){
  if(!isAuthenticated)closeMobileMore();
  $("login").hidden=isAuthenticated;$("dashboard").hidden=!isAuthenticated;
  $("sign-out").hidden=!isAuthenticated;
 }
 async function handleAuth(){
  const {data,error}=await db.auth.getUser();
  const user=data?.user;
  if(error||!user||!ADMIN_EMAILS.has(user.email?.toLowerCase())||!user.email_confirmed_at){
   setLogin(false);
   if(user&&!ADMIN_EMAILS.has(user.email?.toLowerCase())){await db.auth.signOut();toast("Tämä ei ole Kaurivon hallintatili.","error");}
   return;
  }
  setLogin(true);showTab("prospects");await reload();await syncPushStatus();
 }
 // Keep only the pending email in this installed app, never an OTP/link or token.
 const PENDING_LOGIN_KEY="kaurivo_pending_admin_login";
 let pendingLoginEmail="";
 function showLoginVerification(email){
  pendingLoginEmail=email;
  $("login-verify").hidden=false;
  $("login-instructions").textContent=
   "Vahvista tilin "+email+" kirjautuminen tässä Kaurivo-sovelluksessa. "+
   "Avaa Gmail, paina sähköpostin kirjautumislinkkiä pitkään ja valitse Kopioi linkki. "+
   "Älä avaa linkkiä Safarissa.";
 }
 function restorePendingLogin(){
  try{
   const pending=JSON.parse(localStorage.getItem(PENDING_LOGIN_KEY)||"null");
   if(pending && ADMIN_EMAILS.has(pending.email) &&
      Number.isFinite(pending.until) && Date.now()<pending.until){
    $("admin-email").value=pending.email;
    showLoginVerification(pending.email);
   }else localStorage.removeItem(PENDING_LOGIN_KEY);
  }catch(_){localStorage.removeItem(PENDING_LOGIN_KEY);}
 }

 async function passwordLogin(event){
  event.preventDefault();
  const buttonEl=$("password-login");
  if(buttonEl.disabled)return;
  const email=$("admin-email").value.trim().toLowerCase();
  const password=$("admin-password").value;
  if(!ADMIN_EMAILS.has(email)){toast("Tämä ei ole Kaurivon hallintatili.","error");return;}
  if(!password){toast("Anna tilin salasana.","error");return;}
  buttonEl.disabled=true;
  try{
   const {data,error}=await db.auth.signInWithPassword({email,password});
   if(error)throw error;
   const user=data?.user;
   if(!user||!ADMIN_EMAILS.has(user.email?.toLowerCase())||!user.email_confirmed_at){
    await db.auth.signOut();
    throw Error("Kirjautuminen ei ole sallittu tälle tilille.");
   }
   $("admin-password").value="";
   toast("Kirjauduttu Kaurivoon ilman sähköpostivahvistusta.","success");
   await handleAuth();
  }catch(err){
   // Do not expose the entered password, session, or raw backend details.
   const message=String(err?.message||"").toLowerCase();
   const invalid=/invalid login credentials|invalid credentials|invalid_grant|wrong password/.test(message);
   toast(invalid
    ?"Sähköposti tai salasana ei kelpaa. Jos et ole vielä painanut hallintapaneelissa 'Aseta salasana', "+
     "tämä kirjautuminen ei voi onnistua. Avaa alkuperäinen Safari-istunto tai käytä sähköpostilinkkiä kiintiön vapauduttua."
    :"Kirjautuminen ei onnistunut. Varmista ylläpitotili, salasana ja yhteys. "+
     "Jos salasanaa ei ole aiemmin asetettu, käytä kirjautunutta Safari-istuntoa tai sähköpostivahvistusta.","error");
  }finally{buttonEl.disabled=false;}
 }
 async function openPasswordSetup(){
  try{
   const {data:{user},error}=await db.auth.getUser();
   if(error||!user||!ADMIN_EMAILS.has(user.email?.toLowerCase())||!user.email_confirmed_at){
    throw Error("Kirjaudu vahvistetulle ylläpitotilille ennen salasanan asettamista.");
   }
   $("password-account-notice").textContent=
    "Salasana asetetaan nyt tilille "+user.email+
    ". Käytä samaa sähköpostia PWA-sovelluksen kirjautumisessa.";
   $("new-admin-password").value="";
   $("confirm-admin-password").value="";
   $("password-dialog").showModal();
  }catch(err){toast(err.message||"Tilin vahvistus epäonnistui.","error");}
 }
 function closePasswordSetup(){
  $("new-admin-password").value="";
  $("confirm-admin-password").value="";
  $("password-dialog").close();
 }
 async function savePassword(event){
  event.preventDefault();
  const buttonEl=$("save-password");
  if(buttonEl.disabled)return;
  const password=$("new-admin-password").value;
  const check=$("confirm-admin-password").value;
  if(password.length<12||password.length>128){
   toast("Valitse vähintään 12-merkkinen salasana.","error");return;
  }
  if(password!==check){toast("Salasanat eivät täsmää.","error");return;}
  buttonEl.disabled=true;
  try{
   const {data:{user},error:authError}=await db.auth.getUser();
   if(authError||!user||!ADMIN_EMAILS.has(user.email?.toLowerCase())||!user.email_confirmed_at)
    throw Error("Kirjaudu uudelleen vahvistettuun ylläpitotiliin.");
   const {error}=await db.auth.updateUser({password});
   if(error)throw error;
   closePasswordSetup();
   toast("Salasana asetettu tilille "+user.email+
     ". Voit kirjautua sillä Kaurivon aloitusnäytön sovelluksessa.","success");
  }catch(err){
   $("new-admin-password").value="";
   $("confirm-admin-password").value="";
   toast("Salasanaa ei voitu asettaa: "+
    (err?.message||"Tarkista, että Safari-istunto on voimassa.")+
    ". Palvelu voi vaatia tuoreen kirjautumisen.","error");
  }finally{buttonEl.disabled=false;}
 }
 async function sendLogin(){
  const buttonEl=$("send-login");
  if(buttonEl.disabled)return;
  buttonEl.disabled=true;
  try{
   const email=$("admin-email").value.trim().toLowerCase();
   if(!ADMIN_EMAILS.has(email))throw Error("Tämä ei ole sallittu hallintatili.");
   const {error}=await db.auth.signInWithOtp({
    email,options:{emailRedirectTo:REDIRECT_URL,shouldCreateUser:false}
   });
   if(error)throw error;
   localStorage.setItem(PENDING_LOGIN_KEY,
    JSON.stringify({email,until:Date.now()+60*60*1000}));
   showLoginVerification(email);
   $("login-proof").value="";
   toast("Kirjautumisviesti lähetetty. Kopioi Gmailin linkki ja liitä se tähän sovellukseen.","success");
  }catch(err){
   const limited=err?.code==="over_email_send_rate_limit"||
     /email rate limit exceeded/i.test(err?.message||"");
   toast(limited
    ?"Supabasen sähköpostikiintiö täyttyi. Älä tilaa uutta viestiä vielä. "+
     "Käytä salasanakirjautumista tai aseta salasana jo kirjautuneessa Safarissa."
    :"Kirjautumisviestin lähetys epäonnistui: "+(err?.message||"Virhe"),"error");
  }finally{buttonEl.disabled=false;}
 }
 function loginProof(raw){
  const value=String(raw||"").trim();
  if(/^\d{6,8}$/.test(value)){
   return {email:pendingLoginEmail,token:value,type:"email"};
  }
  // Only accept a direct Supabase verification URL for this Kaurivo project.
  // Never navigate to, log or send a pasted URL to a third-party host.
  let url;
  try{url=new URL(value);}catch(_){
   throw Error("Liitä koko Gmailista kopioitu kirjautumislinkki tai numerokoodi.");
  }
  if(url.protocol!=="https:"||url.hostname!=="xhsfbcwpwbgdbatrcyuk.supabase.co"||
     url.port||url.username||url.password||
     !/^\/auth\/v1\/verify\/?$/.test(url.pathname)||
     value.length>4096)
   throw Error("Linkki ei ole Kaurivon virallinen vahvistuslinkki. Kopioi alkuperäinen Gmailista.");
  const token_hash=url.searchParams.get("token")||url.searchParams.get("token_hash");
  const type=url.searchParams.get("type");
  if(!token_hash || token_hash.length>512 ||
     !/^[A-Za-z0-9_-]{16,512}$/.test(token_hash) ||
     !["email","magiclink","signup"].includes(type))
   throw Error("Linkistä puuttuu kelvollinen vahvistustunnus. Tilaa uusi kirjautumisviesti.");
  return {token_hash,type};
 }
 async function verifyLogin(){
  const buttonEl=$("verify-login");
  if(buttonEl.disabled)return;
  buttonEl.disabled=true;
  try{
   if(!ADMIN_EMAILS.has(pendingLoginEmail))
    throw Error("Tilaa kirjautumisviesti ensin.");
   const proof=loginProof($("login-proof").value);
   const {data,error}=await db.auth.verifyOtp(proof);
   if(error)throw error;
   const user=data?.user;
   if(!user || !ADMIN_EMAILS.has(user.email?.toLowerCase()) ||
      !user.email_confirmed_at){
    await db.auth.signOut();
    throw Error("Kaurivon vahvistettua hallintatiliä ei löytynyt.");
   }
   $("login-proof").value="";
   localStorage.removeItem(PENDING_LOGIN_KEY);
   pendingLoginEmail="";
   toast("Kirjautuminen onnistui Kaurivo-sovelluksessa.","success");
   await handleAuth();
  }catch(err){
   toast("Vahvistus epäonnistui: "+(err.message||"Vanhentunut tai jo käytetty linkki.")+
    " Jos avasit linkin jo Safarissa, tilaa uusi viesti ja kopioi uusi linkki avaamatta sitä.","error");
  }finally{buttonEl.disabled=false;}
 }
 async function init(){
  $("redirect-url").textContent=REDIRECT_URL;
  if(!window.supabase?.createClient){toast("Turvallista kirjautumiskirjastoa ei voitu ladata. Päivitä sivu.","error");return;}
  db=window.supabase.createClient(SUPABASE_URL,PUBLIC_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
  document.querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>showTab(b.dataset.tab)));
  document.querySelectorAll("[data-mobile-tab]").forEach(b=>{
   b.addEventListener("click",()=>navigateMobile(b.dataset.mobileTab));
  });
  $("mobile-more-button").addEventListener("click",openMobileMore);
  $("mobile-more-close").addEventListener("click",()=>closeMobileMore(true));
  document.querySelector("[data-close-more]").addEventListener("click",()=>closeMobileMore(true));
  $("mobile-password-setup").addEventListener("click",()=>{closeMobileMore();openPasswordSetup();});
  $("mobile-sign-out").addEventListener("click",()=>{closeMobileMore();$("sign-out").click();});
  document.addEventListener("keydown",event=>{
   if(event.key==="Escape")closeMobileMore(true);
  });
  document.querySelectorAll("[data-dialog]").forEach(b=>b.addEventListener("click",()=>openEditor(b.dataset.dialog)));
  restorePendingLogin();
  $("password-login-form").addEventListener("submit",passwordLogin);
  $("open-password-setup").addEventListener("click",openPasswordSetup);
  $("password-setup-form").addEventListener("submit",savePassword);
  $("close-password-dialog").addEventListener("click",closePasswordSetup);
  $("cancel-password").addEventListener("click",closePasswordSetup);
  $("send-login").addEventListener("click",sendLogin);
  $("verify-login").addEventListener("click",verifyLogin);
  $("login-proof").addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();verifyLogin();}});
  $("sign-out").addEventListener("click",async()=>{await unsubscribePush();await db.auth.signOut();rows={clients:[],projects:[],sales:[],queue:[],reviews:[],invitations:[],prospects:[],events:[]};setLogin(false);});
  $("refresh").addEventListener("click",reload);
  $("start-manual-scan").addEventListener("click",startManualScan);
  $("suppression-form").addEventListener("submit",addSuppression);
  $("show-skipped-prospects").addEventListener("change",render);
  $("lead-view").addEventListener("change",render);
  $("prospect-day").addEventListener("change",async event=>{
   if(!/^\d{4}-\d{2}-\d{2}$/.test(event.target.value))return;
   selectedDay=event.target.value;await reload();showTab("prospects");
  });
  $("enable-push").addEventListener("click",enablePush);
  $("test-push").addEventListener("click",testPush);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden&&$("dashboard").hidden===false)reload();});
  $("import-prospects").addEventListener("click",()=>$("prospect-file").click());
  $("prospect-file").addEventListener("change",async e=>{
   const file=e.target.files?.[0];e.target.value="";
   if(file)await importProspects(file);
  });
  $("editor-form").addEventListener("submit",e=>editing?.kind==="verify_sale"?confirmSale(e):saveEditor(e));
  $("close-editor").addEventListener("click",()=>$("editor").close());
  $("cancel-editor").addEventListener("click",()=>$("editor").close());
  $("close-invite").addEventListener("click",()=>{$("invite-dialog").close();currentInvite=null;$("invite-copy").value="";});
  $("copy-invite").addEventListener("click",copyInvite);
  $("mark-sent").addEventListener("click",()=>markSent());
  db.auth.onAuthStateChange((_event,session)=>{window.setTimeout(()=>{if(session?.user)handleAuth();else setLogin(false);},0);});
  await handleAuth();
 }
 init();
})();