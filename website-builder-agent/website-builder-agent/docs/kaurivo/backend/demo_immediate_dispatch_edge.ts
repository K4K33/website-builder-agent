// Kaurivo admin-only GitHub Actions dispatch.
// NEVER expose the GitHub token to browser, logs or the published website.
// GitHub schedule is retained only as a slow backup; UI calls here on click.
// Configure Supabase secret KAURIVO_GITHUB_DISPATCH_TOKEN as a fine-grained PAT
// limited to K4K33/website-builder-agent with Actions:write.
import {createClient} from "npm:@supabase/supabase-js@2.57.2";

const SB_URL=Deno.env.get("SUPABASE_URL")||"";
const SB_ANON=Deno.env.get("SUPABASE_ANON_KEY")||"";
const GH_TOKEN=Deno.env.get("KAURIVO_GITHUB_DISPATCH_TOKEN")||"";
const ORIGIN="https://k4k33.github.io";
const WORKFLOW="https://api.github.com/repos/K4K33/website-builder-agent/actions/workflows/kaurivo-demo-worker.yml/dispatches";
const cors={"Access-Control-Allow-Origin":ORIGIN,
 "Access-Control-Allow-Methods":"POST, OPTIONS",
 "Access-Control-Allow-Headers":"authorization, apikey, content-type, x-client-info, x-region",
 "Vary":"Origin","Cache-Control":"no-store"};
function reply(status:number,body:Record<string,unknown>){
 return new Response(JSON.stringify(body),{
  status,headers:{...cors,"Content-Type":"application/json;charset=utf-8"}
 });
}
Deno.serve(async req=>{
 if(req.headers.get("origin")!==ORIGIN)return reply(403,{ok:false,reason:"origin_forbidden"});
 if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors});
 if(req.method!=="POST")return reply(405,{ok:false,reason:"method"});
 if(!req.headers.get("content-type")?.startsWith("application/json"))
  return reply(415,{ok:false,reason:"content_type"});
 const auth=req.headers.get("authorization")||"";
 if(!auth.startsWith("Bearer ")||auth.length>5000)return reply(401,{ok:false,reason:"auth_missing"});
 if(!SB_URL||!SB_ANON)return reply(503,{ok:false,reason:"backend_unavailable"});
 let body:Record<string,unknown>;
 try{
  const raw=await req.text();
  if(raw.length>350)return reply(413,{ok:false,reason:"size"});
  body=JSON.parse(raw);
  if(!body||typeof body!=="object"||Array.isArray(body)
     ||Object.keys(body).length!==1)throw Error("shape");
 }catch(_){return reply(400,{ok:false,reason:"invalid_json"});}
 const jobId=body.job_id;
 if(typeof jobId!=="string"||
  !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(jobId))
  return reply(400,{ok:false,reason:"job_id"});
 const userClient=createClient(SB_URL,SB_ANON,{
  auth:{persistSession:false,autoRefreshToken:false},
  global:{headers:{Authorization:auth}}
 });
 const {data:{user},error:authError}=await userClient.auth.getUser(auth.slice(7));
 if(authError||!user)return reply(401,{ok:false,reason:"auth_invalid"});
 // Authenticated user SELECT is protected by the existing ADMIN-ONLY RLS.
 const {data:job,error:dbError}=await userClient
  .from("kaurivo_demo_build_jobs").select("id,status").eq("id",jobId)
  .eq("status","queued").maybeSingle();
 if(dbError)return reply(503,{ok:false,reason:"db_unavailable"});
 if(!job)return reply(403,{ok:false,reason:"admin_queued_job_required"});
 // Persist only allowlisted operational reason codes, never credentials or
 // user data. The UI can then distinguish accepted dispatch from a failed one
 // even after refresh. A failed dispatch is not a failed website build.
 async function reportDispatch(reason:string,accepted=false){
  try{
   const {error}=await userClient.rpc("kaurivo_report_demo_dispatch",{
    p_job_id:jobId,p_error_code:reason,p_accepted:accepted
   });
   if(error)console.warn("Kaurivo dispatch status could not be recorded.");
  }catch(_){console.warn("Kaurivo dispatch status unavailable.");}
 }
 if(!GH_TOKEN){
  await reportDispatch("github_token_not_configured");
  return reply(503,{ok:false,reason:"github_token_not_configured"});
 }
 const {data:claimed,error:claimError}=await userClient
  .rpc("kaurivo_claim_demo_dispatch",{p_job_id:jobId});
 if(claimError){
  await reportDispatch("dispatch_claim_failed");
  return reply(503,{ok:false,reason:"dispatch_claim_failed"});
 }
 if(claimed!==true)return reply(409,{ok:false,reason:"already_requested_or_not_queued"});
 try{
  const response=await fetch(WORKFLOW,{
   method:"POST",
   headers:{"Accept":"application/vnd.github+json",
    "Authorization":"Bearer "+GH_TOKEN,
    "X-GitHub-Api-Version":"2022-11-28",
    "Content-Type":"application/json","User-Agent":"KaurivoDemoDispatcher/1.0"},
   // The worker must claim THIS company, not some older queued prospect.
   // 204 acknowledges dispatch only; the runner's signed claim proves start.
   body:JSON.stringify({ref:"main",inputs:{job_id:jobId}}),
   signal:AbortSignal.timeout(10000)
  });
  // 204 means DISPATCH ACCEPTED, not that the build completed.
  if(response.status===204){
   await reportDispatch("",true);
   return reply(202,{ok:true,dispatch:"accepted"});
  }
  if(response.status===401||response.status===403){
   await reportDispatch("github_token_permissions");
   return reply(503,{ok:false,reason:"github_token_permissions"});
  }
  if(response.status===429){
   await reportDispatch("github_rate_limited");
   return reply(503,{ok:false,reason:"github_rate_limited"});
  }
  await reportDispatch("github_dispatch_failed");
  return reply(502,{ok:false,reason:"github_dispatch_failed"});
 }catch(_){
  await reportDispatch("github_unreachable");
  return reply(503,{ok:false,reason:"github_unreachable"});
 }
});
