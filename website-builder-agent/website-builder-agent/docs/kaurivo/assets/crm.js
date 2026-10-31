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
 let db=null,activeTab="prospects",rows={clients:[],projects:[],sales:[],queue:[],reviews:[],invitations:[],prospects:[]};
 let currentInvite=null,busy=false;
 const label={lead:"Liidi",contacted:"Kontaktoitu",negotiating:"Neuvottelu",customer:"Asiakas",archived:"Arkistoitu",discovery:"Kartoitus",demo:"Demo",proposal:"Tarjous",building:"Rakenteilla",review:"Tarkistus",delivered:"Luovutettu",cancelled:"Peruttu",won:"Voitettu",lost:"Hävitty",pending:"Odottaa",prepared:"Valmisteltu",sent:"Lähetetty",urgent_review:"Kiireellinen",normal_review:"Normaali",clarify:"Tarkennettava",unverified:"Tarkistamatta",researching:"Tutkitaan",needs_demo:"Demoehdokas",ready_for_demo:"Valmis demoon",skipped:"Ohitettu"};
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
 function showTab(tab){activeTab=tab;for(const t of ["prospects","clients","projects","sales","queue","reviews"]){$("tab-"+t).hidden=t!==tab;const b=document.querySelector('[data-tab="'+t+'"]');b.classList.toggle("current",t===tab);b.setAttribute("aria-selected",t===tab?"true":"false");}}
 function render(){
  $("m-clients").textContent=rows.clients.length;
  $("m-projects").textContent=rows.projects.length;
  $("m-sales").textContent=rows.sales.filter(x=>x.status==="won"&&x.source_verified).length;
  $("m-feedback").textContent=rows.queue.filter(x=>x.status==="pending"||x.status==="prepared").length;
  $("now-label").textContent=new Date().toLocaleDateString("fi-FI",{day:"numeric",month:"long",year:"numeric"});
  const prospects=$("prospect-list");prospects.replaceChildren();
  $("prospect-day").value=selectedDay;
  const isToday=selectedDay===helsinkiToday();
  $("morning-summary").textContent=rows.prospects.length
    ? rows.prospects.length+" yritystä · "+selectedDay
    : isToday?"Tämän päivän lista ei ole vielä valmistunut. Tarkista yöajo.":"Ei listaa valitulta päivältä.";
  if(!rows.prospects.length)empty(prospects,"Päivälle "+selectedDay+" ei löydy yrityksiä. Yöajo tai yritysten tuonti on voinut epäonnistua.");
  for(const candidate of rows.prospects){
   const row=record(prospects,candidate.company_name,
     (candidate.city_hint||"Kaupunki tuntematon")+" · Y-tunnus: "+candidate.business_id,
     stage(candidate.review_status));
   const website=String(candidate.website_listed_url||"");
   if(website){
    try{
     const url=new URL(website);
     if(url.protocol==="https:"||url.protocol==="http:"){
      const link=append(row.main,"a","record-website","Avaa nykyinen verkkosivu ↗");
      link.href=url.href;link.target="_blank";link.rel="noopener noreferrer";
      append(row.main,"span","record-sub",url.hostname+" · PRH:n ilmoittama, ei tarkistettu");
     }
    }catch(_){append(row.main,"div","record-sub","Verkkosivulinkki ei ole kelvollinen · tarkista käsin");}
   }else append(row.main,"div","record-no-website","Ei verkkosivua löytynyt · ei vielä vahvistettu");
   append(row.main,"div","record-sub","Toimiala: "+(candidate.industry_code_hint||"ei tietoa")+" · Lähde PRH/YTJ CC BY 4.0");
   if(candidate.research_notes)append(row.main,"div","record-note",candidate.research_notes);
   row.actions.append(button("Tutkimusmuistiinpanot",()=>openEditor("prospect",candidate)));
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
    ["prospects","kaurivo_crm_prospects"],["clients","kaurivo_crm_clients"],["projects","kaurivo_crm_projects"],
    ["sales","kaurivo_crm_sales"],["queue","kaurivo_crm_feedback_queue"],
    ["reviews","kaurivo_feedback_submissions"],["invitations","kaurivo_feedback_invitations"]
   ];
   const results=await Promise.all(entities.map(([key,table])=>{
    let query=db.from(table).select("*");
    if(key==="prospects")return query.eq("discovery_date",selectedDay).order("created_at",{ascending:false}).limit(100);
    return query.order(key==="reviews"?"submitted_at":"created_at",{ascending:false}).limit(250);
   }));
   for(let i=0;i<results.length;i++){
    const {data,error}=results[i];if(error)throw error;rows[entities[i][0]]=data||[];
   }
   render();
  }catch(err){toast("Tietojen lataus epäonnistui. Tarkista käyttöoikeudet: "+(err.message||"tuntematon virhe"),"error");}
  finally{busy=false;}
 }
 const forms={
  prospect:{title:"Yrityksen taustatutkimus",table:"kaurivo_crm_prospects",fields:[
   ["review_status","Tutkimuksen vaihe","choice",true,["unverified","researching","needs_demo","ready_for_demo","skipped"]],
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
  if(value!==undefined&&value!==null)control.value=String(value);
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
   const value=$("field-"+key).value.trim();
   if(required&&!value){toast("Täytä pakolliset kentät.","error");return;}
   data[key]=type==="number"?Number(value):(value||null);
  }
  if(kind==="prospect"){data.research_notes=data.research_notes||"";}
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
   items.push({
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
   status.textContent=sub?"Ilmoitukset käytössä":"Ilmoitukset eivät vielä ole käytössä.";
   test.hidden=!sub;
   $("enable-push").textContent=sub?"Päivitä ilmoitustila":"Salli ilmoitukset";
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
 async function sendLogin(){
  const buttonEl=$("send-login");buttonEl.disabled=true;
  try{
   const {error}=await db.auth.signInWithOtp({
    email:$("admin-email").value,
    options:{emailRedirectTo:REDIRECT_URL,shouldCreateUser:true}
   });
   if(error)throw error;
   toast("Kirjautumislinkki on lähetetty osoitteeseen "+$("admin-email").value+".","success");
  }catch(err){toast("Kirjautumislinkkiä ei voitu lähettää: "+(err.message||"Virhe"),"error");}
  finally{buttonEl.disabled=false;}
 }
 async function init(){
  $("redirect-url").textContent=REDIRECT_URL;
  if(!window.supabase?.createClient){toast("Turvallista kirjautumiskirjastoa ei voitu ladata. Päivitä sivu.","error");return;}
  db=window.supabase.createClient(SUPABASE_URL,PUBLIC_KEY,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}});
  document.querySelectorAll("[data-tab]").forEach(b=>b.addEventListener("click",()=>showTab(b.dataset.tab)));
  document.querySelectorAll("[data-dialog]").forEach(b=>b.addEventListener("click",()=>openEditor(b.dataset.dialog)));
  $("send-login").addEventListener("click",sendLogin);
  $("sign-out").addEventListener("click",async()=>{await unsubscribePush();await db.auth.signOut();rows={clients:[],projects:[],sales:[],queue:[],reviews:[],invitations:[],prospects:[]};setLogin(false);});
  $("refresh").addEventListener("click",reload);
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