import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.95.0/+esm";

const URL = "https://xhsfbcwpwbgdbatrcyuk.supabase.co";
const KEY = "sb_publishable_eESXBcqgycaQXzflfZN34w_nWP2ixvU";
const ADMIN_EMAIL = "hello.kaurivo@gmail.com";
const ADMIN_URL = "https://k4k33.github.io/website-builder-agent/kaurivo/admin/";
const supabase = createClient(URL, KEY, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, flowType: "implicit" }
});
const $ = (id) => document.getElementById(id);
const state = { view:"overview", clients:[], projects:[], sales:[], queue:[], reviews:[], user:null, loading:false, modal:null };
const tables = {
  clients:"kaurivo_crm_clients",projects:"kaurivo_crm_projects",
  sales:"kaurivo_crm_sales",queue:"kaurivo_crm_feedback_queue",
  reviews:"kaurivo_feedback_submissions",invites:"kaurivo_feedback_invitations"
};
const stateLabels = {
  lead:"Liidi",contacted:"Kontaktoitu",negotiating:"Neuvottelu",customer:"Asiakas",archived:"Arkistoitu",
  discovery:"Kartoitus",demo:"Demo",proposal:"Tarjous",building:"Rakennus",review:"Tarkistus",
  delivered:"Luovutettu",cancelled:"Peruttu",won:"Vahvistettu",lost:"Ei toteutunut",
  pending:"Odottaa",prepared:"Valmisteltu",sent:"Lähetetty",
  urgent_review:"Kiireellinen",normal_review:"Tarkistettava",clarify:"Lisätietoja"
};
const currency = new Intl.NumberFormat("fi-FI",{style:"currency",currency:"EUR",maximumFractionDigits:2});
const datefmt = new Intl.DateTimeFormat("fi-FI",{dateStyle:"short",timeStyle:"short"});
const optionSets = {
  clientStatus:[["lead","Liidi"],["contacted","Kontaktoitu"],["negotiating","Neuvottelu"],["customer","Asiakas"],["archived","Arkistoitu"]],
  projectStatus:[["discovery","Kartoitus"],["demo","Demo"],["proposal","Tarjous"],["building","Rakennus"],["review","Tarkistus"],["delivered","Luovutettu"],["cancelled","Peruttu"]],
  saleStatus:[["proposal","Tarjous"],["won","Vahvistettu kauppa"],["lost","Ei toteutunut"]]
};
function stamp(v){try{return v?datefmt.format(new Date(v)):"—";}catch{return "—";}}
function el(tag,opts={},children=[]){
  const n=document.createElement(tag);
  if(opts.className)n.className=opts.className;
  if(opts.text!==undefined)n.textContent=String(opts.text);
  if(opts.title)n.title=opts.title;
  for(const [name,val] of Object.entries(opts.attrs||{}))n.setAttribute(name,val);
  for(const child of children) n.append(child instanceof Node?child:document.createTextNode(String(child)));
  return n;
}
function setEmpty(container,msg){container.replaceChildren(el("div",{className:"empty",text:msg}));}
let toastHandle=null;
function toast(message){const node=$("toast");node.textContent=message;node.hidden=false;clearTimeout(toastHandle);toastHandle=setTimeout(()=>{node.hidden=true},5400);}
function fail(err){toast(err?.message||"Toiminto epäonnistui. Tarkista verkkoyhteys.");}
function label(v){return stateLabels[v]||v||"—";}
function badge(value){return el("span",{className:"pill"+(["won","sent","customer","delivered"].includes(value)?" success": ["urgent_review","lost"].includes(value)?" error":["pending","prepared"].includes(value)?" warning":""),text:label(value)})}
function action(text,onClick,className="row-button"){const b=el("button",{className,text,attrs:{type:"button"}});b.addEventListener("click",onClick);return b;}
function mini(primary,sub,right){return el("div",{className:"mini-item"},[el("div",{},[el("strong",{text:primary}),el("p",{text:sub})]),right||el("span",{text:"↗"})]);}
function setView(view){
  if(!["overview","clients","projects","sales","feedback"].includes(view))return;
  state.view=view;
  for(const v of ["overview","clients","projects","sales","feedback"])$(v+"-view").hidden=v!==view;
  document.querySelectorAll("[data-view]").forEach(n=>n.classList.toggle("active",n.dataset.view===view));
  $("top-title").textContent={overview:"Yhteenveto",clients:"Yritykset",projects:"Projektit",sales:"Kaupat",feedback:"Palaute"}[view];
  $("top-create").textContent=view==="projects"?"+ Uusi projekti":view==="sales"?"+ Kirjaa kauppa":"+ Uusi yritys";
  $("top-create").hidden=view==="feedback";
  window.scrollTo({top:0,behavior:"instant"});
}
function clientFor(id){return state.clients.find(c=>c.id===id)}
function projectFor(id){return state.projects.find(p=>p.id===id)}
function saleFor(id){return state.sales.find(s=>s.id===id)}
function clientName(id){return clientFor(id)?.company_name||"Tuntematon yritys"}
async function refresh(){
  if(!state.user||state.loading)return;
  state.loading=true;$("sync-status").textContent="Synkronoidaan…";
  try{
    const keys=["clients","projects","sales","queue","reviews"];
    const vals=await Promise.all(keys.map(k=>supabase.from(tables[k]).select("*").order("created_at" in {}?"created_at": k==="reviews"?"submitted_at": k==="queue"?"due_at":"created_at",{ascending:false})));
    for(let i=0;i<vals.length;i++){
      if(vals[i].error)throw vals[i].error;
      state[keys[i]]=vals[i].data||[];
    }
    render();
    $("sync-status").textContent="Päivitetty "+new Intl.DateTimeFormat("fi-FI",{hour:"2-digit",minute:"2-digit"}).format(new Date());
  }catch(e){$("sync-status").textContent="Yhteysvirhe";fail(e);}
  finally{state.loading=false;}
}
function render(){
  $("metric-clients").textContent=state.clients.length;
  $("metric-projects").textContent=state.projects.filter(p=>["discovery","demo","proposal","building","review"].includes(p.status)).length;
  $("metric-sales").textContent=state.sales.filter(s=>s.status==="won"&&s.source_verified).length;
  $("metric-reviews").textContent=state.reviews.length;
  renderList("clients");
  renderList("projects");
  renderList("sales");
  renderQueue("feedback-queue",state.queue);
  renderQueue("overview-queue",state.queue.filter(q=>q.status!=="sent").slice(0,4),true);
  const last=state.projects.slice(0,4);
  const mount=$("overview-projects");
  if(!last.length)setEmpty(mount,"Ei projekteja vielä. Lisää ensimmäinen projekti.");
  else mount.replaceChildren(...last.map(p=>mini(p.project_name,clientName(p.client_id),badge(p.status))));
  renderReviews();
}
function renderList(type){
  const mount=$(type+"-list");
  const data=state[type];
  if(!data.length){setEmpty(mount,{clients:"Ei yrityksiä. Aloita lisäämällä ensimmäinen asiakas tai liidi.",projects:"Ei projekteja. Luo projekti yrityksen tietoihin.",sales:"Ei kauppoja. Lisää tarjous tai vahvistettu tilaus."}[type]);return;}
  mount.replaceChildren(...data.map(item=>{
    let cells;
    if(type==="clients"){
      cells=[
        el("div",{},[el("b",{text:item.company_name}),el("small",{text:item.contact_name||"Ei yhteyshenkilöä"})]),
        el("div",{className:"sub",text:item.email}),
        el("div",{},[badge(item.status)]),
        el("div",{},[action("Muokkaa",()=>openForm(type,item))])];
    }else if(type==="projects"){
      cells=[
        el("div",{},[el("b",{text:item.project_name}),el("small",{text:item.editor_platform?"Muokkaus: "+item.editor_platform:"Alusta tarkentamatta"})]),
        el("div",{className:"sub",text:clientName(item.client_id)}),
        el("div",{},[badge(item.status)]),
        el("div",{},[action("Muokkaa",()=>openForm(type,item))])];
    }else{
      cells=[
        el("div",{},[el("b",{text:clientName(item.client_id)}),el("small",{text:stamp(item.confirmed_at||item.created_at)})]),
        el("div",{className:"sub",text:currency.format(item.amount_eur||0)}),
        el("div",{},[badge(item.source_verified&&item.status==="won"?"won":item.status)]),
        el("div",{},[action("Muokkaa",()=>openForm(type,item))])];
    }
    return el("div",{className:"list-row"},cells);
  }));
}
function renderQueue(id,rows,compact=false){
  const mount=$(id);
  if(!rows.length){setEmpty(mount,"Ei odottavia palautepyyntöjä.");return;}
  mount.replaceChildren(...rows.map(q=>{
    const customer=clientFor(q.client_id),sale=saleFor(q.sale_id),due=new Date(q.due_at),ready=due<=new Date();
    const title=customer?.company_name||"Asiakas";
    const sub=stamp(q.due_at)+" · "+label(q.status);
    const options=[];
    if(!compact){
      if(["pending","prepared"].includes(q.status))
        options.push(action(q.status==="prepared"?"Uusi kutsulinkki":"Valmistele kutsu",()=>prepareInvite(q), "row-button"));
      if(q.status==="prepared")
        options.push(action("Merkitse lähetetyksi",()=>markSent(q)));
    }else options.push(badge(q.status));
    if(!ready&&q.status==="pending"&&!compact)options[0].disabled=true;
    const row=el("div",{className:"queue-item"},[
      el("div",{},[el("strong",{text:title}),el("p",{text:sub}),el("p",{text:!ready&&q.status==="pending"?"Valmisteltavissa eräpäivänä":sale?.source_verified?"Vahvistettu kauppa":"Tarkista kaupan vahvistus"})]),
      el("div",{className:"queue-actions"},options)
    ]);
    return row;
  }));
}
function renderReviews(){
  const mount=$("feedback-reviews");
  if(!state.reviews.length){setEmpty(mount,"Ei vielä asiakasarvioita. Testipalautteet näkyvät tässä yksityisesti.");return;}
  mount.replaceChildren(...state.reviews.map(r=>{
    const stars="★".repeat(r.rating)+"☆".repeat(5-r.rating);
    return el("article",{className:"review-item"},[
      el("div",{className:"review-copy"},[
        el("div",{className:"review-meta"},[
          el("span",{className:"stars",text:stars}),badge(r.priority),
          el("span",{className:"pill",text:r.topic||"Palaute"})]),
        el("p",{className:"review-comment",text:r.comment_text}),
        el("p",{text:stamp(r.submitted_at)+(r.source_verified?" · Lähde tarkistettu":" · Ei vielä käsin vahvistettu")})
      ])
    ]);
  }));
}
function inputField(def,values){
  const holder=el("div",{className:"field"+(def.full?" full":"")});
  if(def.type==="checkbox"){
    const inp=el("input",{attrs:{type:"checkbox",name:def.key,id:"field-"+def.key}});
    inp.checked=Boolean(values[def.key]);
    const labelNode=el("label",{className:"check",attrs:{for:"field-"+def.key}},[inp,el("span",{text:def.label})]);
    holder.append(labelNode);
    if(def.help)holder.append(el("small",{text:def.help}));
    return holder;
  }
  const id="field-"+def.key;
  holder.append(el("label",{text:def.label,attrs:{for:id}}));
  const attrs={name:def.key,id,placeholder:def.placeholder||""};
  if(def.required)attrs.required="";
  if(def.min!==undefined)attrs.min=String(def.min);
  if(def.step!==undefined)attrs.step=String(def.step);
  if(def.type==="select"){
    const select=el("select",{attrs});
    const options=def.options||[];
    if(!def.required)select.append(el("option",{text:"Ei valintaa",attrs:{value:""}}));
    for(const [value,title] of options)select.append(el("option",{text:title,attrs:{value}}));
    select.value=String(values[def.key]??"");
    holder.append(select);
  }else{
    const control=def.type==="textarea"?el("textarea",{attrs}):el("input",{attrs:{...attrs,type:def.type||"text"}});
    control.value=values[def.key]===null||values[def.key]===undefined?"":String(values[def.key]);
    if(def.type==="textarea")control.rows=3;
    holder.append(control);
  }
  if(def.help)holder.append(el("small",{text:def.help}));
  return holder;
}
function formSchema(type,item){
  if(type==="clients")return [
    {key:"company_name",label:"Yritys *",required:true,full:true},
    {key:"contact_name",label:"Yhteyshenkilö"},
    {key:"email",label:"Yrityksen sähköposti *",type:"email",required:true},
    {key:"website",label:"Verkkosivusto"},
    {key:"status",label:"Asiakkuuden tila",type:"select",options:optionSets.clientStatus},
    {key:"notes",label:"Muistiinpanot",type:"textarea",full:true}
  ];
  if(type==="projects")return [
    {key:"client_id",label:"Yritys *",type:"select",required:true,full:true,options:state.clients.map(c=>[c.id,c.company_name])},
    {key:"project_name",label:"Projektin nimi *",required:true,full:true},
    {key:"status",label:"Projektin tila",type:"select",options:optionSets.projectStatus},
    {key:"editor_platform",label:"Asiakkaan muokkausalusta",placeholder:"WordPress / muu"},
    {key:"demo_url",label:"Demon osoite",full:true},
    {key:"delivered_url",label:"Valmiin sivuston osoite",full:true},
    {key:"must_haves",label:"Asiakkaan pakolliset toiveet",type:"textarea",full:true},
    {key:"due_date",label:"Tavoitepäivä",type:"date"}
  ];
  return [
    {key:"client_id",label:"Yritys *",type:"select",required:true,full:true,options:state.clients.map(c=>[c.id,c.company_name])},
    {key:"project_id",label:"Liittyvä projekti",type:"select",options:state.projects.map(p=>[p.id,p.project_name+" / "+clientName(p.client_id)])},
    {key:"amount_eur",label:"Sopimussumma (€)",type:"number",min:0,step:.01},
    {key:"status",label:"Kaupan tila",type:"select",options:optionSets.saleStatus},
    {key:"confirmed_at",label:"Kaupan vahvistushetki",type:"datetime-local",help:"Valitse oikea vahvistushetki. Käytetään seuraavan päivän palautepyynnön laskentaan."},
    {key:"source_verified",label:"Kauppa on oikeasti vahvistettu",type:"checkbox",full:true,help:"Valitse vasta, kun olet tarkistanut todellisen tilauksen."},
    {key:"verification_note",label:"Vahvistuksen peruste",type:"textarea",full:true,help:"Esim. hyväksytty tarjous / laskun viite. Älä lisää maksukorttien tai muiden arkaluonteisten tietojen sisältöä."}
  ];
}
function initialValues(type,item){
  if(item){
    const x={...item};
    if(type==="sales"&&x.confirmed_at){
      const d=new Date(x.confirmed_at);
      const local=new Date(d.getTime()-d.getTimezoneOffset()*60000);
      x.confirmed_at=local.toISOString().slice(0,16);
    }
    return x;
  }
  return type==="clients"?{status:"lead"}:type==="projects"?{status:"discovery"}:{status:"proposal",source_verified:false};
}
function openForm(type,item=null){
  if((type==="projects"||type==="sales")&&!state.clients.length){toast("Lisää ensin yritys asiakasrekisteriin.");setView("clients");return;}
  state.modal={type,id:item?.id||null};
  const titles={clients:"yritys",projects:"projekti",sales:"kauppa"};
  $("dialog-eyebrow").textContent=item?"EDIT RECORD":"NEW RECORD";
  $("dialog-title").textContent=(item?"Muokkaa: ":"Uusi ")+titles[type];
  $("dialog-save").disabled=false;
  $("dialog-fields").replaceChildren(...formSchema(type,item).map(f=>inputField(f,initialValues(type,item))));
  $("record-dialog").showModal();
}
function closeForm(){$("record-dialog").close();state.modal=null}
async function saveForm(e){
  e.preventDefault();
  if(!state.modal)return;
  const {type,id}=state.modal;
  const form=$("record-form");
  if(!form.reportValidity())return;
  const body={};
  for(const f of formSchema(type)) {
    const node=form.elements.namedItem(f.key);
    if(!node)continue;
    if(f.type==="checkbox")body[f.key]=node.checked;
    else if(f.type==="number")body[f.key]=Number(node.value||0);
    else if(f.type==="datetime-local")body[f.key]=node.value?new Date(node.value).toISOString():null;
    else body[f.key]=node.value.trim()||((f.key.endsWith("_id")||f.type==="date")?null:"");
  }
  if(type==="sales"){
    if(body.project_id&&projectFor(body.project_id)?.client_id!==body.client_id){
      toast("Valittu projekti kuuluu eri yritykselle.");return;
    }
    if(body.status!=="won"){body.source_verified=false;body.confirmed_at=null;}
    if(body.status==="won" && body.source_verified && (!body.confirmed_at||body.verification_note.length<5)){
      toast("Vahvista kauppa: lisää päivämäärä ja luotettava vahvistuksen peruste.");return;
    }
  }
  $("dialog-save").disabled=true;
  try{
    const query=id?supabase.from(tables[type]).update(body).eq("id",id):supabase.from(tables[type]).insert(body);
    const {error}=await query;
    if(error)throw error;
    closeForm();toast("Tallennettu Kaurivon tietokantaan.");await refresh();
  }catch(e){fail(e);$("dialog-save").disabled=false;}
}
function feedbackEmail(customer,link){
  return {
    subject:"Kaurivo | Miten asiointi sujui?",
    body:"Hei,\n\nKiitos luottamuksesta Kaurivoon! Haluamme kuulla, miten tarjous, yhteydenpito ja kaupan tekeminen sujuivat.\n\nAnna 1–5 tähteä ja kirjoita lyhyt palaute Kaurivon sivulla:\n"+link+
    "\n\nArvio koskee tähänastista asiointia, ei keskeneräistä verkkosivustoa. Vastauksesi pysyy yksityisenä eikä sitä julkaista ilman erillistä lupaa.\n\nKaurivo\nAsiakaskokemus"
  };
}
async function prepareInvite(q){
  if(new Date(q.due_at)>new Date()){toast("Palaute voidaan pyytää vasta eräpäivänä.");return;}
  if(!window.confirm("Valmistellaanko henkilökohtainen kertakäyttöinen palautekutsu? Jos aiempi kutsu oli valmiina, se mitätöidään ja korvataan uudella."))return;
  try{
    const {data:token,error}=await supabase.rpc("kaurivo_crm_prepare_invitation",{p_queue_id:q.id});
    if(error)throw error;
    if(typeof token!=="string"||token.length!==43)throw new Error("Kutsun luonnin vastaus oli virheellinen.");
    const customer=clientFor(q.client_id);
    if(!customer)throw new Error("Asiakasta ei löytynyt.");
    const link="https://k4k33.github.io/website-builder-agent/kaurivo/feedback/?lang=fi#invite="+token;
    const msg=feedbackEmail(customer,link);
    const gmail="https://mail.google.com/mail/?view=cm&fs=1&to="+encodeURIComponent(customer.email)+"&su="+encodeURIComponent(msg.subject)+"&body="+encodeURIComponent(msg.body);
    const content=$("dialog-fields");
    state.modal={type:"invitation"};
    $("dialog-eyebrow").textContent="ONE-TIME PRIVATE LINK";
    $("dialog-title").textContent="Kutsu valmis";
    const note=el("p",{className:"full",text:"Kopioi viesti tai avaa Gmailin kirjoitusnäkymä. Lähetys ei tapahdu automaattisesti. Tarkista vastaanottaja ja lähetä vasta hyväksyttyäsi viestin."});
    const textarea=el("textarea",{className:"full",attrs:{readonly:"",rows:"9"}});
    textarea.value="Vastaanottaja: "+customer.email+"\nAihe: "+msg.subject+"\n\n"+msg.body;
    const copy=action("Kopioi viesti",async()=>{
      try{await navigator.clipboard.writeText(textarea.value);toast("Viesti kopioitu.");}
      catch {textarea.focus();textarea.select();toast("Valitse ja kopioi teksti.");}
    });
    const open=el("a",{className:"primary-button",text:"Avaa Gmail-luonnos ↗",attrs:{href:gmail,target:"_blank",rel:"noopener noreferrer"}});
    const wrap=el("div",{className:"full invite-actions"},[copy,open]);
    content.replaceChildren(note,textarea,wrap);
    $("dialog-save").disabled=true;$("dialog-save").hidden=true;
    $("record-dialog").showModal();
    toast("Kutsu on valmisteltu; sitä ei ole lähetetty.");
    await refresh();
  }catch(e){fail(e);}
}
async function markSent(q){
  if(q.status!=="prepared"||!q.invitation_id){toast("Valmistele kutsu ensin.");return;}
  if(!window.confirm("Vahvista vain, jos olet oikeasti lähettänyt viestin asiakkaalle Kaurivon sähköpostista. Merkitäänkö lähetetyksi?"))return;
  try{
    const {error}=await supabase.from(tables.queue).update({status:"sent",sent_at:new Date().toISOString()}).eq("id",q.id).eq("status","prepared");
    if(error)throw error;
    toast("Kutsu merkitty lähetetyksi.");await refresh();
  }catch(e){fail(e);}
}
async function login(e){
  e.preventDefault();
  const address=$("login-email").value.trim().toLowerCase();
  if(address!==ADMIN_EMAIL){$("login-status").textContent="Tämä työtila on tarkoitettu vain Kaurivon ylläpitotilille.";return;}
  $("login-btn").disabled=true;
  try{
    const {error}=await supabase.auth.signInWithOtp({email:address,options:{emailRedirectTo:ADMIN_URL,shouldCreateUser:true}});
    if(error)throw error;
    $("login-status").textContent="Kirjautumislinkki lähetettiin Kaurivon sähköpostiin. Avaa linkki samassa selaimessa. Jos se ei palauta hallintasivulle, tarkista Supabasen Auth → URL Configuration.";
  }catch(e){$("login-status").textContent=e.message||"Kirjautumisviestin lähetys epäonnistui.";}
  finally{$("login-btn").disabled=false;}
}
async function sessionCheck(){
  try{
    const {data:{user},error}=await supabase.auth.getUser();
    if(error||!user){$("app").hidden=true;$("login-screen").hidden=false;return;}
    // The actual data authorization happens in PostgreSQL RLS.
    if(user.email?.toLowerCase()!==ADMIN_EMAIL||!user.email_confirmed_at){
      $("login-status").textContent="Tällä käyttäjällä ei ole Kaurivon ylläpito-oikeutta.";
      await supabase.auth.signOut();
      $("app").hidden=true;$("login-screen").hidden=false;return;
    }
    const {data, error:accessErr}=await supabase.from(tables.clients).select("id").limit(1);
    if(accessErr)throw accessErr;
    state.user=user;
    $("login-screen").hidden=true;$("app").hidden=false;
    await refresh();
  }catch(e){$("app").hidden=true;$("login-screen").hidden=false;$("login-status").textContent=e.message||"Kirjautumista ei voitu vahvistaa.";}
}
document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
document.querySelectorAll("[data-new]").forEach(b=>b.addEventListener("click",()=>openForm({client:"clients",project:"projects",sale:"sales"}[b.dataset.new])));
$("top-create").addEventListener("click",()=>openForm(state.view==="projects"?"projects":state.view==="sales"?"sales":"clients"));
$("refresh-btn").addEventListener("click",refresh);
$("refresh-feedback").addEventListener("click",refresh);
$("logout-btn").addEventListener("click",async()=>{await supabase.auth.signOut();state.user=null;state.clients=[];state.projects=[];state.sales=[];state.queue=[];state.reviews=[];location.replace(ADMIN_URL)});
$("dialog-cancel").addEventListener("click",closeForm);
$("dialog-close").addEventListener("click",closeForm);
$("record-form").addEventListener("submit",saveForm);
$("record-dialog").addEventListener("close",()=>{$("dialog-save").hidden=false;state.modal=null;});
$("login-form").addEventListener("submit",login);
await sessionCheck();
