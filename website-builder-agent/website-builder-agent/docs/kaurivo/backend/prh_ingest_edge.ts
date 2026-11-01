// Kaurivo nightly official PRH lead ingest — zero static GitHub secrets.
// GitHub Actions OIDC is verified by issuer JWKS, audience and repository claims.
// Only the scheduled/explicitly dispatched national PRH workflow on main may write.
// The service key stays inside this Kaurivo-only Edge Function.
import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";

const jwks = createRemoteJWKSet(
 new URL("https://token.actions.githubusercontent.com/.well-known/jwks")
);
const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk";
const REPOSITORY = "K4K33/website-builder-agent";
const WORKFLOW_REF = REPOSITORY + "/.github/workflows/kaurivo-national-prh.yml@refs/heads/main";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const send = (status: number, body: Record<string, unknown>) =>
 new Response(JSON.stringify(body), {
   status, headers: {"Content-Type":"application/json","Cache-Control":"no-store"}
 });
function clean(value: unknown, max: number) {
 return typeof value === "string" ?
   value.replace(/[\u0000-\u001f\u007f]/g, " ").trim().slice(0,max) : "";
}
function validWebsite(url: string) {
 if(!url)return true;
 try {
  const p=new URL(url);
  return p.protocol==="https:" && !!p.hostname && !p.username && !p.password;
 } catch(_) {return false;}
}
Deno.serve(async req => {
 if(req.method!=="POST")return send(405,{ok:false,error:"method"});
 if(!req.headers.get("content-type")?.startsWith("application/json"))
  return send(415,{ok:false,error:"content_type"});
 const authorization=req.headers.get("authorization") || "";
 if(!authorization.startsWith("Bearer "))return send(401,{ok:false,error:"token_missing"});
 const jwt=authorization.slice(7);
 if(jwt.length>7000)return send(401,{ok:false,error:"token_too_long"});
 try {
  const {payload,protectedHeader}=await jwtVerify(jwt,jwks,{
   issuer:ISSUER,audience:AUDIENCE,algorithms:["RS256"],clockTolerance:"5s"
  });
  if(protectedHeader.alg!=="RS256" ||
     payload.repository!==REPOSITORY ||
     String(payload.repository_id)!=="1376507054" ||
     String(payload.repository_owner_id)!=="327952223" ||
     payload.ref!=="refs/heads/main" ||
     payload.workflow_ref!==WORKFLOW_REF ||
     !["schedule","workflow_dispatch"].includes(String(payload.event_name)) ||
     payload.ref_type!=="branch"
    )return send(403,{ok:false,error:"workflow_not_authorized"});
 }catch(_){return send(401,{ok:false,error:"jwt_invalid"});}
 if(!SUPABASE_URL||!SERVICE_ROLE)return send(503,{ok:false,error:"server_unavailable"});
 if(Number(req.headers.get("content-length")||0)>200000)
  return send(413,{ok:false,error:"size"});
 let data: Record<string, unknown>;
 try {
  const text=await req.text();
  if(text.length>200000)return send(413,{ok:false,error:"size"});
  data=JSON.parse(text);
  if(!data||typeof data!=="object"||Array.isArray(data))throw Error("format");
 } catch(_){return send(400,{ok:false,error:"invalid_json"});}
 // Privacy-preserving feedback: only aggregates from >=8 individually
 // reviewed leads per industry. No personal records or company names leave
 // the server, and the GitHub OIDC gate above applies to this operation.
 if(data.schema==="kaurivo_feedback_weights_v1"){
  if(Object.keys(data).length!==1)return send(400,{ok:false,error:"invalid_feedback_request"});
  try{
   const r=await fetch(SUPABASE_URL+"/rest/v1/rpc/kaurivo_review_feedback_weights",{
    method:"POST",headers:{"apikey":SERVICE_ROLE,"authorization":"Bearer "+SERVICE_ROLE,
     "content-type":"application/json","cache-control":"no-store"},body:"{}"
   });
   if(!r.ok)return send(503,{ok:false,error:"feedback_not_available"});
   const result=await r.json();
   if(!result||typeof result!=="object"||Array.isArray(result))
    return send(503,{ok:false,error:"invalid_feedback"});
   return send(200,{ok:true,weights:result});
  }catch(_){return send(503,{ok:false,error:"feedback_unavailable"});}
 }
 // Separate workflow-failure event. Only the same verified GitHub OIDC
 // workflow may report it; the public PWA cannot submit operational events.
 if(data.schema==="kaurivo_prh_run_status_v1"){
  if(data.outcome!=="failure"||typeof data.date!=="string"||
     !/^\\d{4}-\\d{2}-\\d{2}$/.test(data.date))return send(400,{ok:false,error:"invalid_status"});
  const d=new Date(data.date+"T00:00:00.000Z");
  if(!Number.isFinite(d.getTime())||Math.abs(Date.now()-d.getTime())>2*86400000)
   return send(400,{ok:false,error:"stale_status"});
  const r=await fetch(SUPABASE_URL+"/rest/v1/kaurivo_pipeline_events",{
   method:"POST",headers:{"Content-Type":"application/json",
    "apikey":SERVICE_ROLE,"authorization":"Bearer "+SERVICE_ROLE,
    "prefer":"return=minimal"},
   body:JSON.stringify({event_day:data.date,component:"national_search",
    outcome:"failure",details:"GitHub-yöhaku epäonnistui; tarkista Actions-loki",records:0})
  }).catch(()=>null);
  return send(r?.ok?200:503,{ok:Boolean(r?.ok),status_recorded:Boolean(r?.ok)});
 }
 if(data.schema!=="kaurivo_prh_shortlist_v1"||
    data.mode!=="pilot-live"||
    data.not_verified_for_outreach!==true||
    data.review_required!==true||
    typeof data.date!=="string"||
    !/^\d{4}-\d{2}-\d{2}$/.test(data.date)||
    !Array.isArray(data.candidates)||
    data.candidates.length<1||
    data.candidates.length>50){
   return send(400,{ok:false,error:"invalid_packet"});
 }
 const date=new Date(data.date+"T00:00:00.000Z");
 if(!Number.isFinite(date.getTime()) ||
    Math.abs(Date.now()-date.getTime())>3*86400000){
  return send(400,{ok:false,error:"stale_packet"});
 }
 const candidates: Record<string,unknown>[]=[],used=new Set<string>();
 for(const entry of data.candidates){
  const c=entry as Record<string,unknown>;
  if(!c||typeof c!=="object"||Array.isArray(c)||
   typeof c.business_id!=="string"||
   !/^[0-9]{7}-[0-9]$/.test(c.business_id)||
   c.identity!=="prh:"+c.business_id ||
   c.website_absence_verified!==false ||
   c.business_activity!=="unverified" ||
   c.demo_authorized!==false ||
   c.outreach_authorized!==false ||
   typeof c.name!=="string"||!clean(c.name,160)||
   !validWebsite(clean(c.website_listed_url,1200))){
   return send(400,{ok:false,error:"invalid_candidate"});
  }
  if(used.has(c.business_id))continue;
  used.add(c.business_id);
  // A search hit is NEVER proof of the site's owner, quality or activity.
  const found=c.website_search_candidate as Record<string,unknown> | undefined;
  const source=found&&typeof found==="object" && !Array.isArray(found)
    ?clean(found.source,50):"";
  const confidence=found&&Number.isInteger(found.confidence)
    ?Number(found.confidence):0;
  const candidate=source==="tavily_search" && confidence>=80 && confidence<=99 &&
     typeof found?.url==="string" && validWebsite(clean(found.url,1200))
     ?clean(found.url,1200):"";
  const rawAudit=c.site_technical_audit as Record<string,unknown> | undefined;
  const allowedStatuses=new Set(["html_checked","redirect_not_followed",
   "blocked_or_limited","non_html","html_too_large","temporarily_unavailable",
   "unsafe_or_unresolvable_url"]);
  const status=rawAudit&&typeof rawAudit==="object"&&!Array.isArray(rawAudit)
   ?clean(rawAudit.status,50):"";
  if(status.startsWith("http_status_")&&/^http_status_\d{3}$/.test(status))allowedStatuses.add(status);
  const auditIssues=status==="html_checked"&&Array.isArray(rawAudit?.issues)
   ?rawAudit.issues.filter((i:unknown)=>typeof i==="string" &&
     ["title_missing","meta_description_missing","viewport_missing",
      "heading_missing","contact_link_missing"].includes(i)).slice(0,5):[];
  const technicalAudit=status&&allowedStatuses.has(status)?
   {status,issues:auditIssues,
    title_present:rawAudit?.title_present===true,
    meta_description_present:rawAudit?.meta_description_present===true,
    viewport_present:rawAudit?.viewport_present===true,
    h1_present:rawAudit?.h1_present===true,
    contact_link_present:rawAudit?.contact_link_present===true,
    html_language_hint:["fi","sv","fi_sv","en"].includes(String(rawAudit?.html_language_hint))
     ?rawAudit?.html_language_hint:"undetermined",
    method:"one_public_homepage_html_only"}:{};
  const industry=clean(c.industry_code_hint,20);
  const isTarget=["41","42","43","45","47","49","55","56","69","71","73","74",
    "75","77","79","80","81","82","85","86","90","93","95","96"].some(
       prefix=>industry.startsWith(prefix));
  // Provisional 0..60 research ordering. It is not a prediction of sale,
  // proof of a design flaw, or an actual Lighthouse performance measurement.
  const siteListed=Boolean(clean(c.website_listed_url,1200));
  const preliminary=Math.min(60,(isTarget?25:12)+(siteListed?8:0)+
   (status==="html_checked"?8:0)+Math.min(15,auditIssues.length*3));
  const reasons=[isTarget?"Asiakaspalvelutoimiala":"Toimiala selvitettävä",
    siteListed?"PRH-verkkosivulinkki":"PRH ei ilmoita sivua",
    status==="html_checked"?auditIssues.length+" HTML-metatiedon puutetta (tarkistettava)":
      "Sivuston tekninen tarkistus ei vielä valmis"];
  const screenedReason=reasons.join(" · ").slice(0,500);
  candidates.push({
   business_id:c.business_id,
   company_name:clean(c.name,160),
   city_hint:clean(c.city_hint,80),
   industry_code_hint:clean(c.industry_code_hint,20),
   website_technical_audit:technicalAudit,
   website_audit_checked_at:status&&typeof c.website_audit_checked_at==="string" &&
     !Number.isNaN(Date.parse(c.website_audit_checked_at))?
     new Date(c.website_audit_checked_at).toISOString():null,
   screening_priority:preliminary,
   screening_reason:screenedReason,
   website_listed_url:clean(c.website_listed_url,1200),
   website_candidate_url:candidate,
   website_candidate_source:candidate?source:"",
   website_candidate_confidence:candidate?confidence:0,
   website_candidate_checked_at:candidate?new Date().toISOString():null,
   website_verified:false,
   source_url:"https://avoindata.prh.fi/",
   source_kind:"prh_registry",
   discovery_date:data.date,
   review_status:"unverified",
   activity_verified:false,
   financial_verified:false
  });
 }
 try {
  const result=await fetch(SUPABASE_URL+"/rest/v1/kaurivo_crm_prospects?on_conflict=business_id",{
   method:"POST",
   headers:{
    "Content-Type":"application/json",
    "apikey":SERVICE_ROLE,
    "Authorization":"Bearer "+SERVICE_ROLE,
    "Prefer":"resolution=ignore-duplicates,return=representation"
   },body:JSON.stringify(candidates)
  });
  if(!result.ok){
   return send(503,{ok:false,error:"database_unavailable"});
  }
  let inserted=0;
  try{
   const rows=await result.json();
   if(!Array.isArray(rows))throw Error("invalid_insert_response");
   inserted=rows.length;
  }catch(_){return send(503,{ok:false,error:"database_confirmation_missing"});}
  // Operational evidence is recorded only after PRH candidates were saved.
  const event=await fetch(SUPABASE_URL+"/rest/v1/kaurivo_pipeline_events",{
   method:"POST",headers:{"apikey":SERVICE_ROLE,"authorization":"Bearer "+SERVICE_ROLE,
     "content-type":"application/json","prefer":"return=minimal"},
   body:JSON.stringify({event_day:data.date,component:"national_search",
     outcome:"success",details:"PRH-aineisto tallennettu",records:inserted})
  }).catch(()=>null);
  return send(200,{ok:true,processed:candidates.length,added:inserted,
   report_recorded:Boolean(event?.ok),emails_sent:0,ai_credits_used:0});
 }catch(_){return send(503,{ok:false,error:"database_unavailable"});}
});
