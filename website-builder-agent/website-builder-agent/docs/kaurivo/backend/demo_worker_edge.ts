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
type Work={action?:string;job_id?:string;status?:string;progress?:string;
 preview_url?:string;qa_url?:string;release_sha?:string;error_code?:string};
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
Deno.serve(async request=>{
 if(request.method!=="POST")return reply(405,{ok:false,error:"method"});
 if(!SUPABASE_URL||!SERVICE_ROLE)return reply(503,{ok:false,error:"backend_unavailable"});
 const authorization=request.headers.get("authorization")||"";
 if(!authorization.startsWith("Bearer ")||authorization.length>7200)
  return reply(401,{ok:false,error:"missing_oidc"});
 let run_id=0;
 try{
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
  if(data.action==="claim"){
   if(Object.keys(data).length!==1)return reply(400,{ok:false,error:"claim_args"});
   const run_url="https://github.com/"+REPOSITORY+"/actions/runs/"+run_id;
   const result=await rpc("kaurivo_worker_claim_demo",{
    p_run_id:run_id,p_run_url:run_url
   });
   const job=Array.isArray(result)?result[0]||null:null;
   return reply(200,{ok:true,job});
  }
  if(data.action==="update"){
   if(typeof data.job_id!=="string"||
     !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(data.job_id)||
     !["researching","building","qa","publishing","internal_preview","hold","failed"].includes(data.status||""))
     return reply(400,{ok:false,error:"update_args"});
   const cleaned=typeof data.progress==="string"?data.progress.slice(0,300):"";
   const code=typeof data.error_code==="string"&&/^[a-z0-9_]{0,80}$/.test(data.error_code)
      ?data.error_code:"";
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