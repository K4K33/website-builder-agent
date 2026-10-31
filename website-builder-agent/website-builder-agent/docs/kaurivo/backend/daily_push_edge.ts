// Kaurivo-only PWA Web Push. No credentials are exposed in the static website.
// GitHub Actions OIDC authorizes daily delivery; Supabase Auth authorizes devices.
import { generateVapidKeys } from "npm:@mmmike/web-push@1.5.0/vapid";
import { sendPushNotification } from "npm:@mmmike/web-push@1.5.0/send";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";

const ORIGIN = "https://k4k33.github.io";
const ADMIN_URL = ORIGIN + "/website-builder-agent/kaurivo/admin/";
const URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const AUDIENCE = "kaurivo-morning-push-xhsfbcwpwbgdbatrcyuk";
const WORKFLOW = "K4K33/website-builder-agent/.github/workflows/kaurivo-morning-push.yml@refs/heads/main";
const ALLOWED_EMAILS = new Set(["hello.kaurivo@gmail.com","kaarlo.kaukko1@gmail.com"]);
const JWKS = createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));

function headers() {
 return {"Content-Type":"application/json","Cache-Control":"no-store",
  "Access-Control-Allow-Origin":ORIGIN,
  "Access-Control-Allow-Headers":"authorization,content-type,apikey,x-client-info",
  "Access-Control-Allow-Methods":"GET,POST,OPTIONS",
  "Vary":"Origin"};
}
function reply(status:number, body:Record<string,unknown>){
 return new Response(JSON.stringify(body),{status,headers:headers()});
}
function helsinkiDay(now=new Date()):string {
 const values=new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/Helsinki",
  year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(now);
 const part=(type:string)=>values.find(x=>x.type===type)?.value || "00";
 return part("year")+"-"+part("month")+"-"+part("day");
}
function helsinkiHour(now=new Date()):number {
 return Number(new Intl.DateTimeFormat("en-GB",{timeZone:"Europe/Helsinki",
  hour:"2-digit",hourCycle:"h23"}).format(now));
}
function rest(path:string,init:RequestInit={}):Promise<Response> {
 const headers=new Headers(init.headers);
 headers.set("apikey",SERVICE_KEY);
 headers.set("authorization","Bearer "+SERVICE_KEY);
 if(init.body)headers.set("content-type","application/json");
 return fetch(URL+"/rest/v1/"+path,{...init,headers});
}
async function adminUser(req:Request):Promise<{id:string,email:string}|null>{
 const auth=req.headers.get("authorization")||"";
 const token=auth.startsWith("Bearer ")?auth.slice(7):"";
 if(!token||token.length>7000)return null;
 const result=await fetch(URL+"/auth/v1/user",{headers:{
   apikey:SERVICE_KEY,authorization:"Bearer "+token
 }});
 if(!result.ok)return null;
 const user=await result.json();
 if(typeof user?.id!=="string"||typeof user.email!=="string" ||
   !ALLOWED_EMAILS.has(user.email.toLowerCase()) || !user.email_confirmed_at)return null;
 return {id:user.id,email:user.email.toLowerCase()};
}
async function githubOIDC(req:Request):Promise<{event:string}|null>{
 const auth=req.headers.get("authorization")||"";
 const token=auth.startsWith("Bearer ")?auth.slice(7):"";
 if(token.length<100||token.length>7000)return null;
 try {
  const {payload,protectedHeader}=await jwtVerify(token,JWKS,{
    issuer:"https://token.actions.githubusercontent.com",audience:AUDIENCE,
    algorithms:["RS256"],clockTolerance:"5s"
  });
  if(protectedHeader.alg!=="RS256"||
    payload.repository!=="K4K33/website-builder-agent"||
    String(payload.repository_id)!=="1376507054"||
    String(payload.repository_owner_id)!=="327952223"||
    payload.ref!=="refs/heads/main"||
    payload.ref_type!=="branch"||
    payload.workflow_ref!==WORKFLOW||
    !["schedule","workflow_dispatch"].includes(String(payload.event_name)))return null;
  return {event:String(payload.event_name)};
 }catch(_){return null;}
}
type Keys={public_key:string,private_key:string};
async function vapidKeys():Promise<Keys>{
 let response=await rest("kaurivo_push_vapid?id=eq.1&select=public_key,private_key");
 if(!response.ok)throw new Error("vapid_read");
 let data=await response.json();
 if(data.length===1)return data[0] as Keys;
 const created=await generateVapidKeys();
 response=await rest("kaurivo_push_vapid?on_conflict=id",{
  method:"POST",headers:{"prefer":"resolution=ignore-duplicates,return=minimal"},
  body:JSON.stringify({id:1,public_key:created.publicKey,private_key:created.privateKey})
 });
 if(!response.ok)throw new Error("vapid_save");
 response=await rest("kaurivo_push_vapid?id=eq.1&select=public_key,private_key");
 if(!response.ok)throw new Error("vapid_reload");
 data=await response.json();
 if(data.length!==1)throw new Error("vapid_missing");
 return data[0] as Keys;
}
type Sub={id:string,user_id:string,endpoint:string,p256dh:string,auth_secret:string,last_notified_date:string|null};
async function subscriptions(query:string):Promise<Sub[]>{
 const result=await rest("kaurivo_push_subscriptions?"+query);
 if(!result.ok)throw new Error("subscription_read");
 return await result.json();
}
async function deliver(sub:Sub,payload:Record<string,unknown>,keys:Keys,day?:string):Promise<boolean>{

 try {
  const sent=await sendPushNotification({
    endpoint:sub.endpoint,keys:{p256dh:sub.p256dh,auth:sub.auth_secret}
  },payload as {title:string;body:string;url:string;tag:string},{
    publicKey:keys.public_key,privateKey:keys.private_key,
    subject:"mailto:hello.kaurivo@gmail.com"
  });
  if(!sent){
   await rest("kaurivo_push_subscriptions?id=eq."+encodeURIComponent(sub.id),{method:"DELETE"});
   return false;
  }
  if(day){
   const update=await rest("kaurivo_push_subscriptions?id=eq."+encodeURIComponent(sub.id),{
    method:"PATCH",body:JSON.stringify({last_notified_date:day,updated_at:new Date().toISOString()})
   });
   if(!update.ok)throw new Error("notification_marker");
  }
  return true;
 }catch(err){
  const status=Number((err as {statusCode?:number})?.statusCode||0);
  if(status===404||status===410){
   await rest("kaurivo_push_subscriptions?id=eq."+encodeURIComponent(sub.id),{method:"DELETE"});
  }
  // Push tokens and provider response bodies must never appear in logs.
  return false;
 }
}
async function notifyDaily(event:string):Promise<Response>{
 const day=helsinkiDay();
 if(event==="schedule"&&helsinkiHour()!==8)
  return reply(200,{ok:true,skipped:"outside_08_helsinki",day});
 const result=await rest("kaurivo_crm_prospects?discovery_date=eq."+day+
  "&select=business_id&limit=100");
 if(!result.ok)throw new Error("prospects_unavailable");
 const leads=await result.json();
 const count=leads.length;
 if(!count)return reply(200,{ok:true,day,companies:0,notifications:0,reason:"no_verified_feed_for_today"});
 const subs=await subscriptions("select=id,user_id,endpoint,p256dh,auth_secret,last_notified_date&limit=100");
 const pending=subs.filter(s=>s.last_notified_date!==day);
 if(!pending.length)return reply(200,{ok:true,day,companies:count,notifications:0,reason:"already_sent"});
 const keys=await vapidKeys();
 let delivered=0;
 for(const sub of pending){
  const sent=await deliver(sub,{
   title:"Kaurivo · päivän yritykset",
   body:count+" uutta yritystä tarkistettavana. Avaa aamun lista.",
   url:ADMIN_URL+"?view=prospects&day="+day,tag:"kaurivo-leads-"+day
  },keys,day);
  if(sent)delivered++;
 }
 return reply(200,{ok:true,day,companies:count,notifications:delivered});
}
Deno.serve(async (req:Request)=>{
 if(!URL||!SERVICE_KEY)return reply(503,{ok:false,error:"server_configuration"});
 const origin=req.headers.get("origin");
 if(origin&&origin!==ORIGIN)return reply(403,{ok:false,error:"origin_denied"});
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:headers()});
 if(req.method==="GET"){
  const user=await adminUser(req);
  if(!user)return reply(401,{ok:false,error:"admin_required"});
  try{return reply(200,{ok:true,publicKey:(await vapidKeys()).public_key});}
  catch(_){return reply(503,{ok:false,error:"keys_unavailable"});}
 }
 if(req.method!=="POST")return reply(405,{ok:false,error:"method"});
 if(Number(req.headers.get("content-length")||0)>5000)
   return reply(413,{ok:false,error:"too_large"});
 let body:Record<string,unknown>;
 try {
  const raw=await req.text();
  if(raw.length>5000)throw new Error("large");
  body=JSON.parse(raw);
  if(!body||typeof body!=="object"||Array.isArray(body))throw new Error("invalid");
 }catch(_){return reply(400,{ok:false,error:"invalid_body"});}
 const action=body.action;
 if(action==="notify"){
  const oidc=await githubOIDC(req);
  if(!oidc)return reply(403,{ok:false,error:"workflow_not_authorized"});
  try{return await notifyDaily(oidc.event);}
  catch(_){return reply(503,{ok:false,error:"delivery_unavailable"});}
 }
 const user=await adminUser(req);
 if(!user)return reply(401,{ok:false,error:"admin_required"});
 if(action==="subscribe"){
  const sub=body.subscription as Record<string,unknown> | undefined;
  const ks=sub?.keys as Record<string,unknown> | undefined;
  const endpoint=typeof sub?.endpoint==="string"?sub.endpoint:"";
  const p256dh=typeof ks?.p256dh==="string"?ks.p256dh:"";
  const auth=typeof ks?.auth==="string"?ks.auth:"";
  let valid=false;
  try{
   const u=new URL(endpoint);
   valid=u.protocol==="https:"&&!u.username&&!u.password&&
    u.hostname.includes(".")&&endpoint.length<=2048;
  }catch(_){}
  if(!valid||!/^[-_A-Za-z0-9]{20,300}$/.test(p256dh)||
    !/^[-_A-Za-z0-9]{10,150}$/.test(auth))
   return reply(400,{ok:false,error:"invalid_subscription"});
  try{
   const current=await subscriptions("user_id=eq."+user.id+"&select=id,endpoint&limit=20");
   if(current.length>=8&&!current.some(x=>x.endpoint===endpoint))
    return reply(429,{ok:false,error:"devices_limit"});
   const result=await rest("kaurivo_push_subscriptions?on_conflict=endpoint",{
    method:"POST",headers:{"prefer":"resolution=merge-duplicates,return=minimal"},
    body:JSON.stringify({user_id:user.id,endpoint,p256dh,auth_secret:auth,
       updated_at:new Date().toISOString()})
   });
   if(!result.ok)throw new Error("save");
   return reply(200,{ok:true,subscribed:true});
  }catch(_){return reply(503,{ok:false,error:"subscription_unavailable"});}
 }
 if(action==="unsubscribe"){
  const endpoint=typeof body.endpoint==="string"?body.endpoint:"";
  if(!endpoint)return reply(400,{ok:false,error:"invalid_endpoint"});
  try {
   const result=await rest("kaurivo_push_subscriptions?user_id=eq."+user.id+
       "&endpoint=eq."+encodeURIComponent(endpoint),{method:"DELETE"});
   if(!result.ok)throw new Error("delete");
   return reply(200,{ok:true,subscribed:false});
  }catch(_){return reply(503,{ok:false,error:"subscription_unavailable"});}
 }
 if(action==="test"){
  try{
   const subs=await subscriptions("user_id=eq."+user.id+
     "&select=id,user_id,endpoint,p256dh,auth_secret,last_notified_date&limit=8");
   const keys=await vapidKeys();
   let sent=0;
   for(const sub of subs){
    if(await deliver(sub,{
     title:"Kaurivo · testiviesti",body:"Ilmoitukset ovat käytössä. Avaa liidijono.",
     url:ADMIN_URL+"?view=prospects",tag:"kaurivo-test"
    },keys))sent++;
   }
   return reply(200,{ok:sent>0,sent});
  }catch(_){return reply(503,{ok:false,error:"test_failed"});}
 }
 return reply(400,{ok:false,error:"unknown_action"});
});
