// Kaurivo admin-only manual PRH backup search; never a replacement for nightly nationwide ZIP.
// No AI credits, no generated business data, no outreach; only PRH registry facts.
const SB_URL=Deno.env.get("SUPABASE_URL")||"";
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
const ORIGIN="https://k4k33.github.io";
const API="https://avoindata.prh.fi/opendata-ytj-api/v3/companies";
const ADMINS=new Set(["hello.kaurivo@gmail.com","kaarlo.kaukko1@gmail.com"]);
const CITIES=["Helsinki","Espoo","Tampere","Turku","Oulu","Jyväskylä","Lahti",
 "Kuopio","Pori","Joensuu","Vaasa","Lappeenranta","Rovaniemi","Kouvola",
 "Seinäjoki","Vantaa","Hämeenlinna","Salo","Kotka","Kajaani","Mikkeli","Kokkola",
 "Rauma","Lohja"];
const MAX_REQUESTS=6;
const PROPERTY_NAME=/(?:asunto[ -]?osake(?:yhtiö|yhtiö)|asunto[ -]?oy|\bas\.?\s*oy\b|bostads(?:aktiebolag|\s*ab|\s*aktiebolag)|kiinteistö(?:osake(?:yhtiö)?|[ -]+oy\b)|keskinäinen\s+kiinteistö|fastighets(?:aktiebolag|\s*ab)|\b(?:holding|investments?|sijoitusyhtiö|sijoitus\s*oy)\b)/i;
const EXCLUDED_INDUSTRY=["6820","6810","6420","6430","6499"];
const CUSTOMER_SECTORS=["41","42","43","45","47","49","55","56","69","71","73","74","75","77","79","80","81","82","85","86","90","93","95","96","6831","6832"];
const OTHER_SECTORS=["10","11","13","14","16","18","20","22","23","25","26","27","28","29","31","32","33","46","50","52","58","59","60","62","63","70","72"];
function businessScore(name:string,industry:string):number{
 if(PROPERTY_NAME.test(name)||EXCLUDED_INDUSTRY.some(p=>industry.startsWith(p)))return -1;
 if(CUSTOMER_SECTORS.some(p=>industry.startsWith(p)))return 4;
 if(OTHER_SECTORS.some(p=>industry.startsWith(p)))return 2;
 return 0;
}

function headers(){return {"Content-Type":"application/json","Cache-Control":"no-store",
 "Access-Control-Allow-Origin":ORIGIN,
 "Access-Control-Allow-Methods":"GET,POST,OPTIONS",
 "Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info","Vary":"Origin"};}
function reply(status:number,body:Record<string,unknown>):Response{
 return new Response(JSON.stringify(body),{status,headers:headers()});
}
function today():string {
 const parts=new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/Helsinki",
  year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());
 const x=(p:string)=>parts.find(k=>k.type===p)?.value||"00";
 return x("year")+"-"+x("month")+"-"+x("day");
}
async function rest(path:string,init:RequestInit={}):Promise<Response>{
 const h=new Headers(init.headers);
 h.set("apikey",SERVICE_KEY);h.set("Authorization","Bearer "+SERVICE_KEY);
 if(init.body)h.set("Content-Type","application/json");
 return fetch(SB_URL+"/rest/v1/"+path,{...init,headers:h});
}
async function checkAdmin(req:Request):Promise<boolean>{
 const authorization=req.headers.get("Authorization")||"";
 if(!authorization.startsWith("Bearer ")||authorization.length>7200)return false;
 const resp=await fetch(SB_URL+"/auth/v1/user",{
  headers:{apikey:SERVICE_KEY,authorization}
 });
 if(!resp.ok)return false;
 const user=await resp.json();
 return !!user?.email_confirmed_at&&ADMINS.has(String(user.email||"").toLowerCase());
}
async function currentRun(day:string){
 const r=await rest("kaurivo_manual_scan_runs?run_day=eq."+day+
  "&select=run_day,attempts,status,examined,added,updated_at");
 if(!r.ok)throw Error("status_unavailable");
 const arr=await r.json();return arr[0]||null;
}
function normalize(rec:Record<string,unknown>){
 if(rec.endDate||!rec.businessId||!Array.isArray(rec.names))return null;
 const bid=(rec.businessId as {value?:unknown}).value;
 if(typeof bid!=="string"||!/^[0-9]{7}-[0-9]$/.test(bid))return null;
 const names=rec.names as Array<Record<string,unknown>>;
 const nameRecord=names.find(n=>n.version===1&&!n.endDate&&typeof n.name==="string"&&n.name.trim())||
  names.find(n=>!n.endDate&&typeof n.name==="string"&&n.name.trim());
 const name=String(nameRecord?.name||"").replace(/[\u0000-\u001f\u007f]/g," ").trim().slice(0,160);
 if(name.length<2)return null;
 const situations=Array.isArray(rec.companySituations)?rec.companySituations as Array<{type?:string,endDate?:string}>:[];
 if(situations.some(x=>["KONK","SELTILA","SANE"].includes(x.type||"")&&!x.endDate))return null;
 const offices=Array.isArray(rec.addresses)?rec.addresses as Array<Record<string,unknown>>:[];
 let city="";
 for(const address of offices){
  const post=Array.isArray(address.postOffices)?address.postOffices as Array<{city?:string,name?:string}>:[];
  city=String(post.find(x=>x.city||x.name)?.city||post.find(x=>x.city||x.name)?.name||"").slice(0,80);
  if(city)break;
 }
 const websiteObject=rec.website;
 let website=typeof websiteObject==="object"&&websiteObject?String((websiteObject as {url?:unknown}).url||""):"";
 website=website.trim();
 if(website&&!website.includes("://"))website="https://"+website;
 try{const u=new globalThis.URL(website);
  website=["http:","https:"].includes(u.protocol)&&!u.username&&!u.password?u.href.slice(0,1200):"";
 }catch(_){website="";}
 const industry=rec.mainBusinessLine;
 const industryCode=typeof industry==="object"&&industry?
  String((industry as {type?:unknown}).type||"").slice(0,20):"";
 if(businessScore(name,industryCode)<2)return null;
 return {business_id:bid,company_name:name,city_hint:city,industry_code_hint:industryCode,
  website_listed_url:website,source_url:"https://avoindata.prh.fi/",
  source_kind:"prh_registry",discovery_date:today(),review_status:"unverified",
  activity_verified:false,website_verified:false,financial_verified:false};
}
function selectedCities(day:string,attempt:number):string[]{
 const base=(Number(day.replaceAll("-",""))+attempt*7)%CITIES.length;
 // Spread the six lookups geographically instead of repeatedly using big cities.
 const picks=[] as string[];
 for(let i=0;i<MAX_REQUESTS;i++)picks.push(CITIES[(base+i*5)%CITIES.length]);
 return picks;
}
async function recordManualEvent(day:string,outcome:"success"|"failure",details:string,records:number){
 await rest("kaurivo_pipeline_events",{method:"POST",
  headers:{"Prefer":"return=minimal"},
  body:JSON.stringify({event_day:day,component:"manual_search",outcome,details,records})
 }).catch(()=>null);
}
async function runSearch(day:string):Promise<Record<string,unknown>>{
 const result=await rest("rpc/kaurivo_claim_manual_scan",{method:"POST",
  body:JSON.stringify({p_day:day})});
 if(!result.ok)throw Error("claim_failed");
 const claimed=await result.json();
 if(claimed!==true)return {ok:false,reason:"cooldown_or_daily_limit",run:await currentRun(day)};
 const current=await currentRun(day);
 const attempt=Number(current?.attempts)||1;
 let examined=0,added=0,requests=0,validQueries=0;
 try{
  const pool=new Map<string,ReturnType<typeof normalize>>();
  for(const city of selectedCities(day,attempt)){
   const query=new globalThis.URL(API);
   query.searchParams.set("location",city);
   query.searchParams.set("companyForm","OY");
   query.searchParams.set("page",String(Math.min(attempt,3)));
   const response=await fetch(query.toString(),{
    headers:{"Accept":"application/json","User-Agent":"KaurivoRegistryResearch/1.0"},
    signal:AbortSignal.timeout(12000)
   });
   requests++;
   if(response.status===429)break; // Honor provider rate-limit; never retry automatically.
   if(!response.ok)continue;
   const blob=await response.text();
   if(blob.length>1500000)continue;
   const parsed=JSON.parse(blob);
   if(!Array.isArray(parsed?.companies))continue;
   validQueries++;
   examined+=parsed.companies.length;
   for(const raw of parsed.companies.slice(0,100)){
    const entity=normalize(raw);
    if(entity)pool.set(entity.business_id,entity);
   }
  }
  if(validQueries===0)throw Error("prh_unavailable");
  const eligible=Array.from(pool.values()).filter(Boolean) as NonNullable<ReturnType<typeof normalize>>[];
  // Score the actual business type first. Balance known and unknown website
  // records only if the PRH source provides known websites.
  eligible.sort((a,b)=>{
   const score=businessScore(b.company_name,b.industry_code_hint)-
    businessScore(a.company_name,a.industry_code_hint);
   if(score)return score;
   // Stable day-specific spread; avoid alphabetically returning the same oldest firms.
   const hash=(x:string)=>{
    let n=2166136261;for(const char of day+"|"+x){n^=char.charCodeAt(0);n=Math.imul(n,16777619);}
    return n>>>0;
   };
   return hash(a.business_id)-hash(b.business_id);
  });
  const withUrl=eligible.filter(x=>!!x.website_listed_url);
  const withoutUrl=eligible.filter(x=>!x.website_listed_url);
  const selected:typeof eligible=[];
  // Don't force exactly 50 or make up websites when the source has none.
  const counts=new Map<string,number>();
  for(let i=0;i<50;i++){
   let next=null as (typeof eligible)[number]|null;
   for(const pool of i%2?[withUrl,withoutUrl]:[withoutUrl,withUrl]){
    const idx=pool.findIndex(x=>(counts.get(x.industry_code_hint)||0)<6);
    if(idx>=0){next=pool.splice(idx,1)[0];break;}
   }
   if(!next)break;
   selected.push(next);
   counts.set(next.industry_code_hint,(counts.get(next.industry_code_hint)||0)+1);
  }
  if(selected.length){
   const insert=await rest("kaurivo_crm_prospects?on_conflict=business_id",{
    method:"POST",headers:{"Prefer":"resolution=ignore-duplicates,return=representation"},
    body:JSON.stringify(selected)
   });
   if(!insert.ok)throw Error("save_failed");
   const inserted=await insert.json();
   added=Array.isArray(inserted)?inserted.length:0;
  }
  const done=await rest("kaurivo_manual_scan_runs?run_day=eq."+day,{
   method:"PATCH",body:JSON.stringify({status:"succeeded",examined,added,updated_at:new Date().toISOString()})
  });
  if(!done.ok)throw Error("status_save_failed");
  await recordManualEvent(day,"success","Rajattu PRH-varahaku valmis",added);
  return {ok:true,day,examined,added,requests,valid_queries:validQueries,
   ai_credits_used:0,marketing_emails_sent:0,
   note:"Varahaku kattaa kuusi aluehakua, ei koko valtakunnallista PRH-aineistoa."};
 }catch(_){
  await rest("kaurivo_manual_scan_runs?run_day=eq."+day,{
   method:"PATCH",body:JSON.stringify({status:"failed",examined,added,updated_at:new Date().toISOString()})
  }).catch(()=>{});
  await recordManualEvent(day,"failure","PRH-varahaun lähde tai tallennus epäonnistui",0);
  return {ok:false,reason:"provider_or_storage_failed",day,requests};
 }
}
Deno.serve(async(req:Request)=>{
 if(req.headers.get("Origin")&&req.headers.get("Origin")!==ORIGIN)
  return reply(403,{ok:false,reason:"origin_denied"});
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:headers()});
 if(!SB_URL||!SERVICE_KEY)return reply(503,{ok:false,reason:"server_config"});
 if(!["GET","POST"].includes(req.method))return reply(405,{ok:false,reason:"method"});
 try{
  if(!await checkAdmin(req))return reply(401,{ok:false,reason:"admin_required"});
  const day=today();
  if(req.method==="GET")return reply(200,{ok:true,day,run:await currentRun(day)});
  if(Number(req.headers.get("Content-Length")||"0")>100)return reply(413,{ok:false,reason:"too_large"});
  const body=await req.json().catch(()=>null);
  if(body?.action!=="scan")return reply(400,{ok:false,reason:"invalid_action"});
  const result=await runSearch(day);
  return reply(result.ok?200:result.reason==="cooldown_or_daily_limit"?429:503,result);
 }catch(_){return reply(503,{ok:false,reason:"temporary_unavailable"});}
});
