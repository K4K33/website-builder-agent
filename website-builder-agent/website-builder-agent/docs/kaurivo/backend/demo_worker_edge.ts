// Dedicated Kaurivo demo builder bridge. Browser uses ONLY the admin RLS RPC
// to enqueue. This endpoint accepts ONLY a short-lived GitHub Actions OIDC JWT
// from the exact approved workflow in the exact K4K33 repo/main.
import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";

const JWKS=createRemoteJWKSet(new URL("https://token.actions.githubusercontent.com/.well-known/jwks"));
const SUPABASE_URL=Deno.env.get("SUPABASE_URL")||"";
const SERVICE_ROLE=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
const AUDIENCE="kaurivo-demo-worker-xhsfbcwpwbgdbatrcyuk";
const OWNER="327952223",REPOSITORY_ID="1376507054";
const REPOSITORY="K4K33/website-builder-agent";
const WORKFLOW_REF=REPOSITORY+"/.github/workflows/kaurivo-demo-worker.yml@refs/heads/main";
const reply=(status:number,value:Record<string,unknown>)=>new Response(JSON.stringify(value),{
 status,headers:{"content-type":"application/json;charset=utf-8","cache-control":"no-store",
  "x-content-type-options":"nosniff","vary":"Authorization"}
});
type Work={action?:string;job_id?:string;ready?:boolean;backend?:string;status?:string;progress?:string;
 preview_url?:string;qa_url?:string;release_sha?:string;error_code?:string;key_http_status?:number};
async function rpc(name:string,body:Record<string,unknown>){
 const resp=await fetch(SUPABASE_URL+"/rest/v1/rpc/"+name,{
  method:"POST",
  headers:{apikey:SERVICE_ROLE,authorization:"Bearer "+SERVICE_ROLE,
   "content-type":"application/json","cache-control":"no-store"},
  body:JSON.stringify(body)
 });
 if(!resp.ok)throw Error("database_rpc");
 return await resp.json();
}
const CHECKPOINT_BUCKET="kaurivo-demo-checkpoints";
const CHECKPOINT_MAX_BYTES=31457280;
const CHECKPOINT_STAGES=new Set(["research_partial","researched","concepts","selected","built","revised_1","revised_2"]);
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SHA=/^[0-9a-f]{64}$/;
type Checkpoint={stage:string;checksum:string;object_path:string;byte_count:number};
async function checkpointMeta(job:string,run:number):Promise<Checkpoint|null>{
 const rows=await rpc("kaurivo_worker_checkpoint_get",{p_id:job,p_run_id:run});
 const found=Array.isArray(rows)?rows[0]||null:null;
 if(!found)return null;
 if(!CHECKPOINT_STAGES.has(found.stage)||!SHA.test(found.checksum)||
    found.object_path!==job+"/"+found.checksum+".zip"||
    !Number.isSafeInteger(found.byte_count)||found.byte_count<1||
    found.byte_count>CHECKPOINT_MAX_BYTES)throw Error("invalid_checkpoint_record");
 return found;
}
function objectUrl(path:string):string{
 return SUPABASE_URL+"/storage/v1/object/"+CHECKPOINT_BUCKET+"/"+path;
}
function storageHeaders():Record<string,string>{
 return {apikey:SERVICE_ROLE,authorization:"Bearer "+SERVICE_ROLE,
  "cache-control":"no-store"};
}
async function shaHex(buffer:ArrayBuffer):Promise<string>{
 const digest=new Uint8Array(await crypto.subtle.digest("SHA-256",buffer));
 return [...digest].map(b=>b.toString(16).padStart(2,"0")).join("");
}
Deno.serve(async request=>{
 if(request.method!=="POST")return reply(405,{ok:false,error:"method"});
 if(!SUPABASE_URL||!SERVICE_ROLE)return reply(503,{ok:false,error:"backend_unavailable"});
 const authorization=request.headers.get("authorization")||"";
 if(!authorization.startsWith("Bearer ")||authorization.length>7200)
  return reply(401,{ok:false,error:"missing_oidc"});
 let run_id=0;
 const local=authorization.startsWith("Bearer kvl_");
 if(local){
  // A separate, owner-enrolled device identity. No browser admin JWT,
  // service-role key, password or GitHub OIDC key is stored on Windows.
  const token=authorization.slice(7);
  if(!/^kvl_[0-9a-f]{64}$/.test(token))
   return reply(403,{ok:false,error:"invalid_local_worker"});
  const digest=[...new Uint8Array(await crypto.subtle.digest(
    "SHA-256",new TextEncoder().encode(token)))]
   .map(v=>v.toString(16).padStart(2,"0")).join("");
  try{
   run_id=Number(await rpc("kaurivo_local_worker_validate_v2",{
     p_digest:digest,p_ready:null,p_backend:null
   }));
   if(!Number.isSafeInteger(run_id)||run_id<2000000000000000)
    return reply(403,{ok:false,error:"local_worker_not_enrolled"});
  }catch(_){return reply(503,{ok:false,error:"local_worker_auth_unavailable"});}
 }else try{
  const {payload,protectedHeader}=await jwtVerify(authorization.slice(7),JWKS,{
   issuer:"https://token.actions.githubusercontent.com",
   audience:AUDIENCE,algorithms:["RS256"],clockTolerance:"5s"
  });
  if(protectedHeader.alg!=="RS256"||payload.repository!==REPOSITORY||
   String(payload.repository_id)!==REPOSITORY_ID||
   String(payload.repository_owner_id)!==OWNER||
   payload.ref!=="refs/heads/main"||
   payload.workflow_ref!==WORKFLOW_REF||
   payload.ref_type!=="branch"||
   !["schedule","workflow_dispatch","push"].includes(String(payload.event_name)))throw Error("workflow");
  run_id=Number(payload.run_id);
  if(!Number.isSafeInteger(run_id)||run_id<=0)throw Error("run_id");
 }catch(_){return reply(403,{ok:false,error:"unauthorized_workflow"});}
 // Only the currently claimed run may PUT/GET its own private checkpoint.
 // Browser/admin users cannot authenticate as this GitHub workflow.
 const mode=new URL(request.url).searchParams.get("checkpoint");
 if(mode){
  if(mode!=="write")return reply(400,{ok:false,error:"checkpoint_mode"});
  const params=new URL(request.url).searchParams;
  const job=params.get("job_id")||"";
  const phase=params.get("stage")||"";
  const checksum=params.get("sha256")||"";
  const length=Number(request.headers.get("content-length")||0);
  if(!UUID.test(job)||!CHECKPOINT_STAGES.has(phase)||!SHA.test(checksum)||
     !Number.isSafeInteger(length)||length<1||length>CHECKPOINT_MAX_BYTES||
     (request.headers.get("content-type")||"").split(";")[0]!=="application/zip")
   return reply(400,{ok:false,error:"checkpoint_args"});
  try{
   const allowed=await rpc("kaurivo_worker_checkpoint_can_write",{
    p_id:job,p_run_id:run_id});
   if(allowed!==true)return reply(403,{ok:false,error:"checkpoint_not_claimed"});
   const previous=await checkpointMeta(job,run_id);
   const data=await request.arrayBuffer();
   if(data.byteLength!==length||data.byteLength>CHECKPOINT_MAX_BYTES||
      await shaHex(data)!==checksum)
    return reply(422,{ok:false,error:"checkpoint_integrity"});
   const path=job+"/"+checksum+".zip";
   const stored=await fetch(objectUrl(path),{
    method:"POST",headers:{...storageHeaders(),"content-type":"application/zip",
                             "x-upsert":"false"},body:data});
   if(!stored.ok){
    // An identical content-addressed archive can already exist when an
    // earlier Storage upload succeeded but its DB acknowledgement failed.
    if(stored.status!==409)return reply(503,{ok:false,error:"checkpoint_store"});
    const existing=await fetch(SUPABASE_URL+"/storage/v1/object/authenticated/"+
      CHECKPOINT_BUCKET+"/"+path,{headers:storageHeaders()});
    if(!existing.ok)return reply(503,{ok:false,error:"checkpoint_store"});
    const bytes=await existing.arrayBuffer();
    if(bytes.byteLength!==length||await shaHex(bytes)!==checksum)
     return reply(503,{ok:false,error:"checkpoint_store_integrity"});
   }
   const recorded=await rpc("kaurivo_worker_checkpoint_record",{
    p_id:job,p_run_id:run_id,p_stage:phase,p_checksum:checksum,p_bytes:length});
   if(recorded!==true)return reply(409,{ok:false,error:"checkpoint_not_recorded"});
   // Delete only a prior unreferenced snapshot; failure to prune never
   // downgrades the verified current pointer or exposes private bytes.
   if(previous&&previous.object_path!==path){
    await fetch(SUPABASE_URL+"/storage/v1/object/"+CHECKPOINT_BUCKET,{
      method:"DELETE",headers:{...storageHeaders(),"content-type":"application/json"},
      body:JSON.stringify({prefixes:[previous.object_path]})}).catch(()=>{});
   }
   return reply(200,{ok:true,stage:phase,sha256:checksum,byte_count:length});
  }catch(_){return reply(503,{ok:false,error:"checkpoint_backend_unavailable"});}
 }
 if(Number(request.headers.get("content-length")||0)>4096)
  return reply(413,{ok:false,error:"size"});
 let data:Work;
 try{
  const raw=await request.text();
  if(raw.length>4096)throw Error("large");
  data=JSON.parse(raw);
  if(!data||typeof data!=="object"||Array.isArray(data))throw Error("format");
 }catch(_){return reply(400,{ok:false,error:"invalid_json"});}
 try{
  if(data.action==="ping"&&local){
   const keys=Object.keys(data);
   if((keys.length!==3&&keys.length!==4)
      ||keys.some(key=>!["action","ready","job_id","backend"].includes(key))
      ||data.backend!=="ollama" ||typeof data.ready!=="boolean"
      ||(data.job_id!==undefined &&
         (typeof data.job_id!=="string"||!UUID.test(data.job_id))))
     return reply(400,{ok:false,error:"ping_args"});
   const token=authorization.slice(7);
   const digest=[...new Uint8Array(await crypto.subtle.digest(
    "SHA-256",new TextEncoder().encode(token)))]
    .map(v=>v.toString(16).padStart(2,"0")).join("");
   const result=await rpc("kaurivo_local_worker_validate_v2",{
    p_digest:digest,p_ready:data.ready,p_backend:"ollama"
   });
   if(Number(result)!==run_id)
    return reply(403,{ok:false,error:"local_worker_not_enrolled"});
   // Only heartbeat an actual currently live child process. An idle
   // authenticated daemon must NEVER keep crashed builds falsely alive.
   const leaseActive=typeof data.job_id==="string"?
      await rpc("kaurivo_local_worker_heartbeat",{
        p_id:data.job_id,p_run_id:run_id
      }):false;
   return reply(200,{ok:true,run_id,lease_active:leaseActive===true});
  }
  if(data.action==="release"&&local){
   if(Object.keys(data).length!==2||
      typeof data.job_id!=="string"||!UUID.test(data.job_id))
    return reply(400,{ok:false,error:"release_args"});
   const resumed=await rpc("kaurivo_local_worker_release",{
      p_id:data.job_id,p_run_id:run_id
   });
   // False means job already has terminal status: never fake a retry.
   return reply(200,{ok:true,requeued:resumed===true});
  }
  if(local&&data.action==="health")
    return reply(400,{ok:false,error:"github_health_only"});
  if(data.action==="health"){
   if(Object.keys(data).length!==2||
      !Number.isSafeInteger(data.key_http_status)||
      ![0,200,401,403,429,500].includes(data.key_http_status!))
      return reply(400,{ok:false,error:"invalid_health"});
   const saved=await rpc("kaurivo_worker_record_health",{
     p_run_id:run_id,p_http_status:data.key_http_status!
   });
   return reply(saved===true?200:503,{ok:saved===true});
  }
  if(data.action==="checkpoint_info"||data.action==="checkpoint_read"){
   if(Object.keys(data).length!==2||typeof data.job_id!=="string"||
      !UUID.test(data.job_id))
    return reply(400,{ok:false,error:"checkpoint_args"});
   const allowed=await rpc("kaurivo_worker_checkpoint_can_write",{
    p_id:data.job_id,p_run_id:run_id});
   if(allowed!==true)return reply(403,{ok:false,error:"checkpoint_not_claimed"});
   const info=await checkpointMeta(data.job_id,run_id);
   if(data.action==="checkpoint_info")
    return reply(200,{ok:true,checkpoint:info?{
      stage:info.stage,sha256:info.checksum,byte_count:info.byte_count}:null});
   if(!info)return reply(404,{ok:false,error:"checkpoint_absent"});
   const response=await fetch(SUPABASE_URL+"/storage/v1/object/authenticated/"+
     CHECKPOINT_BUCKET+"/"+info.object_path,{headers:storageHeaders()});
   if(!response.ok)return reply(503,{ok:false,error:"checkpoint_fetch"});
   const bytes=await response.arrayBuffer();
   if(bytes.byteLength!==info.byte_count||await shaHex(bytes)!==info.checksum)
    return reply(503,{ok:false,error:"checkpoint_integrity"});
   return new Response(bytes,{status:200,headers:{
    "content-type":"application/zip","cache-control":"no-store",
    "x-content-type-options":"nosniff","x-checkpoint-stage":info.stage,
    "x-checkpoint-sha256":info.checksum,"vary":"Authorization"}});
  }
  if(data.action==="claim"){
   const keys=Object.keys(data);
   if(keys.length>2||keys.some(key=>!["action","job_id"].includes(key))||
      (data.job_id!==undefined &&
       (typeof data.job_id!=="string"||!UUID.test(data.job_id))))
      return reply(400,{ok:false,error:"claim_args"});
   if(local){
    if(Object.keys(data).length!==1)
     return reply(400,{ok:false,error:"local_claim_args"});
    const result=await rpc("kaurivo_local_worker_claim",{p_run_id:run_id});
    const job=Array.isArray(result)?result[0]||null:null;
    return reply(200,{ok:true,job,run_id});
   }
   const run_url="https://github.com/"+REPOSITORY+"/actions/runs/"+run_id;
   // An explicitly clicked Rakenna demo job gets priority. Scheduled and
   // push backups still claim oldest eligible via the legacy RPC.
   const targeted=typeof data.job_id==="string";
   const result=await rpc(targeted?"kaurivo_worker_claim_specific_demo":
       "kaurivo_worker_claim_demo",targeted?
       {p_run_id:run_id,p_run_url:run_url,p_job_id:data.job_id}:
       {p_run_id:run_id,p_run_url:run_url});
   const job=Array.isArray(result)?result[0]||null:null;
   return reply(200,{ok:true,job});
  }
  if(data.action==="update"){
   if(typeof data.job_id!=="string"||
     !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(data.job_id)||
     !["queued","researching","building","qa","publishing","internal_preview","hold","failed"].includes(data.status||""))
     return reply(400,{ok:false,error:"update_args"});
   const cleaned=typeof data.progress==="string"?data.progress.slice(0,300):"";
   const code=typeof data.error_code==="string"&&/^[a-z0-9_]{0,80}$/.test(data.error_code)
      ?data.error_code:"";
   if(data.status==="queued"&&![
      "free_ai_capacity_unavailable","free_ai_rate_limit",
      "research_network_unavailable","network_unavailable",
      "source_http_rate_limited","stage_timeout","runner_stale_timeout"
     ].includes(code))return reply(400,{ok:false,error:"invalid_defer_code"});
   const updated=await rpc("kaurivo_worker_update_demo",{
    p_id:data.job_id,p_run_id:run_id,p_status:data.status,
    p_progress:cleaned,p_preview_url:typeof data.preview_url==="string"?data.preview_url:"",
    p_qa_url:typeof data.qa_url==="string"?data.qa_url:"",
    p_release_sha:typeof data.release_sha==="string"?data.release_sha:"",
    p_error_code:code
   });
   return reply(updated===true?200:409,{ok:updated===true});
  }
  return reply(400,{ok:false,error:"unknown_action"});
 }catch(_){return reply(503,{ok:false,error:"worker_backend_unavailable"});}
});