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
  candidates.push({
   business_id:c.business_id,
   company_name:clean(c.name,160),
   city_hint:clean(c.city_hint,80),
   industry_code_hint:clean(c.industry_code_hint,20),
   website_listed_url:clean(c.website_listed_url,1200),
   source_url:"https://avoindata.prh.fi/",
   source_kind:"prh_registry",
   discovery_date:data.date,
   review_status:"unverified",
   activity_verified:false,
   website_verified:false,
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
    "Prefer":"resolution=ignore-duplicates,return=minimal"
   },body:JSON.stringify(candidates)
  });
  if(!result.ok){
   return send(503,{ok:false,error:"database_unavailable"});
  }
  return send(200,{ok:true,processed:candidates.length,emails_sent:0,ai_credits_used:0});
 }catch(_){return send(503,{ok:false,error:"database_unavailable"});}
});
