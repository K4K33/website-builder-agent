// Owner-only one-time Windows worker enrollment. No model, GitHub,
// Supabase service-role or PAT secrets are returned to the browser.
// Register a 256-bit generated bearer secret; database stores only its hash.
import {createClient} from "npm:@supabase/supabase-js@2.57.2";

const URL=Deno.env.get("SUPABASE_URL")||"";
const ANON=Deno.env.get("SUPABASE_ANON_KEY")||"";
const ORIGIN="https://k4k33.github.io";
const cors={
 "Access-Control-Allow-Origin":ORIGIN,
 "Access-Control-Allow-Headers":"authorization,apikey,content-type,x-client-info",
 "Access-Control-Allow-Methods":"OPTIONS,POST",
 "Vary":"Origin","Cache-Control":"no-store"
};
function response(code:number,data:Record<string,unknown>){
 return new Response(JSON.stringify(data),{status:code,
  headers:{...cors,"Content-Type":"application/json;charset=utf-8"}});
}
const hex=(v:Uint8Array)=>[...v].map(n=>n.toString(16).padStart(2,"0")).join("");
Deno.serve(async req=>{
 if(req.headers.get("origin")!==ORIGIN)return response(403,{ok:false,reason:"origin_forbidden"});
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 if(req.method!=="POST")return response(405,{ok:false,reason:"method"});
 if(!URL||!ANON)return response(503,{ok:false,reason:"backend_unavailable"});
 if(!req.headers.get("content-type")?.startsWith("application/json"))
  return response(415,{ok:false,reason:"content_type"});
 const authorization=req.headers.get("authorization")||"";
 if(!authorization.startsWith("Bearer ")||authorization.length>5000)
  return response(401,{ok:false,reason:"auth_missing"});
 try{
  const raw=await req.text();
  if(raw.length>128||JSON.parse(raw)?.action!=="enroll")
   return response(400,{ok:false,reason:"invalid_request"});
 }catch(_){return response(400,{ok:false,reason:"invalid_request"});}
 const db=createClient(URL,ANON,{
  auth:{persistSession:false,autoRefreshToken:false},
  global:{headers:{Authorization:authorization}}
 });
 const {data:{user},error}=await db.auth.getUser(authorization.slice(7));
 if(error||!user||!user.email_confirmed_at)
  return response(401,{ok:false,reason:"auth_invalid"});
 const random=crypto.getRandomValues(new Uint8Array(32));
 const token="kvl_"+Array.from(random,n=>String.fromCharCode(n))
   .map(c=>c.charCodeAt(0).toString(16).padStart(2,"0")).join("");
 const digest=hex(new Uint8Array(await crypto.subtle.digest(
   "SHA-256",new TextEncoder().encode(token))));
 const idbytes=crypto.getRandomValues(new Uint8Array(6));
 const runId=2000000000000000+idbytes.reduce((n,v)=>n*256+v,0);
 const result=await db.rpc("kaurivo_local_worker_enroll",{
   p_digest:digest,p_run_id:runId
 });
 if(result.error||result.data!==true)
  return response(403,{ok:false,reason:"admin_required"});
 // This value is NEVER logged or persisted in cleartext. Rotating invalidates
 // previously enrolled Windows processes; owner must store it securely.
 return response(200,{ok:true,token,warning:"Save this token once; it cannot be recovered."});
});
