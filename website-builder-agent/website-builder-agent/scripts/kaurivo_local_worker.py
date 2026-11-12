"""Owner-enrolled, free-only Windows demo builder.

Uses Supabase Realtime wakeups with a 90-second safety poll.
No Codex, GitHub Actions, service-role token or paid AI is used for inference.
The existing brand, source-fidelity and independent QA pipeline stays intact.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

import requests

BASE=Path(__file__).resolve().parents[1]
EDGE="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-demo-worker"
OLLAMA="http://127.0.0.1:11434"
TOKEN_RE=re.compile(r"^kvl_[0-9a-f]{64}$")
UUID_RE=re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$",re.I)
# Event-triggered startup over Realtime, NOT a costly 1 Hz Edge Function loop.
# Missed messages are recovered by a rare poll so the owner's request persists.
FALLBACK_POLL_SECONDS=90.0
PING_SECONDS=20.0
PUBLIC_KEY="sb_publishable_eESXBcqgycaQXzflfZN34w_nWP2ixvU"


class LocalWorkerError(RuntimeError):
    pass


def models() -> dict[str,str]:
    if os.environ.get("KAURIVO_WINDOWS_BACKEND","ollama").strip().lower()!="ollama":
        raise LocalWorkerError("Codex is not allowed in the Kaurivo Windows worker; use local Ollama.")
    result={
        "research":os.environ.get("OLLAMA_RESEARCH_MODEL","qwen2.5-coder:7b").strip(),
        "builder":os.environ.get("OLLAMA_BUILDER_MODEL","qwen2.5-coder:7b").strip(),
        "qa":os.environ.get("OLLAMA_QA_MODEL","llava:7b").strip(),
    }
    if not all(result.values()) or any(v.endswith(":cloud") for v in result.values()):
        raise LocalWorkerError("Only installed local Ollama models are allowed.")
    if result["builder"]==result["qa"]:
        raise LocalWorkerError("Builder and independent visual QA must use different local models.")
    return result


def ollama_ready(session:requests.Session, names:dict[str,str]) -> bool:
    try:
        response=session.get(OLLAMA+"/api/tags",timeout=3,allow_redirects=False)
        response.raise_for_status()
        all_models=response.json().get("models",[])
        installed={str(m.get("name") or "") for m in all_models if isinstance(m,dict)}
        for model in set(names.values()):
            if model not in installed and model+":latest" not in installed:
                return False
        # A generic text-only model must never impersonate independent
        # screenshot-based QA.
        detail=session.post(OLLAMA+"/api/show",json={"model":names["qa"]},
                            timeout=5,allow_redirects=False)
        detail.raise_for_status()
        capabilities=detail.json().get("capabilities",[])
        return isinstance(capabilities,list) and "vision" in capabilities
    except (requests.RequestException,ValueError,KeyError):
        return False


def server(session:requests.Session,token:str,action:str,**kwargs)->dict:
    response=session.post(EDGE,
        headers={"authorization":"Bearer "+token,
                 "content-type":"application/json"},
        json={"action":action,**kwargs},timeout=12,allow_redirects=False)
    response.raise_for_status()
    data=response.json()
    if data.get("ok") is not True:
        raise LocalWorkerError("Private worker rejected "+action+" request.")
    return data


def realtime_wakeup(token:str,wake:threading.Event,keep_running:threading.Event) -> None:
    """Low-latency, secret-topic, payload-free Supabase Broadcast listener.

    The topic is derived from the 256-bit device key; no token or business
    identity is transmitted over the public channel. It only WAKES the
    authenticated claim RPC. The websocket never receives a job record.
    """
    import websocket
    digest=hashlib.sha256(token.encode("ascii")).hexdigest()[:48]
    topic="realtime:kaurivo-demo-local-"+digest
    uri=("wss://xhsfbcwpwbgdbatrcyuk.supabase.co/realtime/v1/websocket"
         "?apikey="+PUBLIC_KEY+"&vsn=1.0.0")
    while keep_running.is_set():
        ws=None
        try:
            ws=websocket.create_connection(uri,timeout=12,
                origin="https://k4k33.github.io",enable_multithread=True)
            ws.settimeout(2.0)
            ws.send(json.dumps({
                "topic":topic,"event":"phx_join","ref":"1","join_ref":"1",
                "payload":{"config":{
                    "broadcast":{"ack":False,"self":False},
                    "presence":{"enabled":False},
                    "private":False}}
            },separators=(",",":")))
            last_heartbeat=time.monotonic()
            joined=False
            while keep_running.is_set():
                if time.monotonic()-last_heartbeat>20:
                    ws.send(json.dumps({"topic":"phoenix","event":"heartbeat",
                        "payload":{},"ref":"2"},separators=(",",":")))
                    last_heartbeat=time.monotonic()
                try:
                    raw=ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if not raw:break
                if not isinstance(raw,str) or len(raw)>6000:continue
                try:packet=json.loads(raw)
                except ValueError:continue
                if not isinstance(packet,dict):continue
                if packet.get("topic")!=topic:continue
                kind=packet.get("event")
                payload=packet.get("payload")
                if not isinstance(payload,dict):payload={}
                if kind=="phx_reply" and packet.get("ref")=="1":
                    if payload.get("status")!="ok":break
                    joined=True
                    wake.set()  # Also recover requests created before join.
                elif kind in ("phx_error","phx_close"):
                    break
                elif joined and kind=="broadcast" and payload.get("event")=="wake":
                    wake.set()
        except (websocket.WebSocketException,OSError,ValueError):
            # Never log the websocket URL/token or prospect metadata.
            pass
        finally:
            if ws is not None:
                try:ws.close()
                except OSError:pass
        if keep_running.is_set():
            for _ in range(5):
                if not keep_running.is_set():break
                time.sleep(1)


def singleton_lock():
    """An exclusive lock, held for the lifetime of this one-user worker."""
    lockfile=Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())/"Kaurivo"
    lockfile.mkdir(parents=True,exist_ok=True)
    file=(lockfile/"worker.lock").open("a+b")
    file.seek(0)
    file.write(b"x")
    file.flush()
    file.seek(0)
    if os.name=="nt":
        import msvcrt
        try:msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as error:
            file.close()
            raise LocalWorkerError("Kaurivo is already running on this computer.") from error
    else:
        import fcntl
        try:fcntl.flock(file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as error:
            file.close()
            raise LocalWorkerError("Kaurivo is already running.") from error
    return file


def run_claim(job:dict,run_id:int,token:str,model_names:dict[str,str]) -> None:
    job_id=str(job.get("id") or "")
    if not UUID_RE.fullmatch(job_id) or type(run_id)!=int or run_id<2000000000000000:
        raise LocalWorkerError("Invalid authenticated local claim.")
    # The original worker checks that this file is inside RUNNER_TEMP and
    # requires the exact claimed job. No other company can be substituted.
    with tempfile.TemporaryDirectory(prefix="kaurivo-local-") as tmp:
        claim=Path(tmp)/"claim.json"
        claim.write_text(json.dumps({"job":job},ensure_ascii=False),encoding="utf-8")
        backend="ollama"  # No Codex or metered cloud fallback, even if env was altered.
        env=os.environ.copy()
        env.update({
           "KAURIVO_LOCAL_WORKER":"1",
           "KAURIVO_LOCAL_WORKER_TOKEN":token,
           "KAURIVO_CLAIMED_JOB_FILE":str(claim),
           "RUNNER_TEMP":tmp,"GITHUB_RUN_ID":str(run_id),
           "FREE_ONLY":"1","AI_BACKEND":backend,
           "RESEARCH_AI_BACKEND":backend,
           "BUILDER_AI_BACKEND":backend,
           "QA_AI_BACKEND":backend,
           "KAURIVO_CODEX_RESEARCH_MODEL":model_names["research"],
           "KAURIVO_CODEX_BUILDER_MODEL":model_names["builder"],
           "KAURIVO_CODEX_QA_MODEL":model_names["qa"],
           "KAURIVO_BROWSER_SOURCE_FALLBACK":"1",
           "FREE_CLOUD_LOCAL_FALLBACK":"1",
           "OLLAMA_RESEARCH_MODEL":model_names["research"],
           "OLLAMA_BUILDER_MODEL":model_names["builder"],
           "OLLAMA_QA_MODEL":model_names["qa"],
           "OLLAMA_MODEL":model_names["builder"],
        })
        # Git credentials for the private preview deployment must already be
        # configured in Windows Git Credential Manager; never print secrets.
        completed=subprocess.run(
            [sys.executable,"-m","scripts.run_kaurivo_demo_queue"],
            cwd=BASE,env=env,check=False)
        if completed.returncode:
            print("Kaurivo: worker exited with a nonzero code; the job state is preserved.",
                  flush=True)


def execute_claim(session:requests.Session,token:str,job:dict,run_id:int,
                  model_names:dict[str,str],active_job:dict) -> None:
    """Run one verified job and always release any unfinished subprocess lease.

    Neither a successful quality HOLD nor a verified finished preview is
    reopened by the server; only unexpectedly still-active jobs are requeued.
    """
    job_id=str(job.get("id") or "")
    if not UUID_RE.fullmatch(job_id):
        raise LocalWorkerError("Invalid claimed demo ID.")
    active_job["id"]=job_id
    try:
        run_claim(job,run_id,token,model_names)
    finally:
        active_job["id"]=None
        try:
            server(session,token,"release",job_id=job_id)
        except (requests.RequestException,LocalWorkerError,ValueError):
            print("Kaurivo: vapautus odottaa yhteyden palaamista; "
                  "vanhentunut työ palautuu automaattisesti.",flush=True)


def main() -> int:
    token=os.environ.get("KAURIVO_LOCAL_WORKER_TOKEN","").strip()
    if not TOKEN_RE.fullmatch(token):
        raise LocalWorkerError("Windows setup token missing or invalid.")
    model_names=models()

    def ai_ready(session):
        # Check only locally installed models; no Codex usage or cloud credits.
        return ollama_ready(session,model_names)

    file=singleton_lock()
    with file,requests.Session() as session:
        print("Kaurivo Windows-rakentaja käynnissä. Realtime-heräte käytössä; varatarkistus 90 s.",
              flush=True)
        worker_id=None
        ready_before=None
        last_model_check=0.0
        keep_running=threading.Event()
        keep_running.set()
        wake=threading.Event()
        wake.set()  # Always check pending durable jobs on first startup.
        # The process lease is deliberately separate from the idle daemon.
        # A crashed child must not be kept alive by the daemon's own heartbeat.
        active_job={"id":None}
        # A local model may take more than 70 minutes. Keep a separate
        # Session and thread so the SQL lease stays fresh through inference.
        def safe_heartbeat():
            with requests.Session() as ping_session:
                while keep_running.is_set():
                    try:
                        lease=active_job["id"]
                        server(ping_session,token,"ping",
                               ready=ai_ready(ping_session),
                               **({"job_id":lease} if lease else {}))
                    except (requests.RequestException,LocalWorkerError,ValueError):
                        pass
                    # Event.wait(true) would spin, so use shutdown-aware sleep.
                    for _ in range(int(PING_SECONDS)):
                        if not keep_running.is_set():break
                        time.sleep(1)
        thread=threading.Thread(target=safe_heartbeat,daemon=True)
        thread.start()
        listener=threading.Thread(target=realtime_wakeup,
            args=(token,wake,keep_running),daemon=True)
        listener.start()
        try:
            while True:
                # Recheck model readiness every 10 seconds, but poll the DB
                # every second while ready. /api/show is not an inference
                # call, yet fetching model metadata each second is wasteful.
                now=time.monotonic()
                if ready_before is None or now-last_model_check>=10:
                    ready=ai_ready(session)
                    last_model_check=now
                else:
                    ready=ready_before
                if ready!=ready_before:
                    print("Kaurivo local AI "+("valmis" if ready else "ei vielä valmis")+
                          " (paikallinen Ollama; erillinen kuvallinen QA-malli).",
                          flush=True)
                    ready_before=ready
                if not ready:
                    time.sleep(5)
                    continue
                # The wake event normally arrives within a second of the
                # admin's request. No HTTP polling is done while idle.
                wake.wait(timeout=FALLBACK_POLL_SECONDS)
                wake.clear()
                try:
                    data=server(session,token,"claim")
                    job=data.get("job")
                    if job:
                        worker_id=int(data["run_id"])
                        job_id=str(job.get("id") or "")
                        print("Kaurivo aloittaa valitun yrityksen rakennustyön.",flush=True)
                        execute_claim(session,token,job,worker_id,
                                      model_names,active_job)
                        # Drain any additional queued companies without
                        # waiting for another notification.
                        wake.set()
                except (requests.RequestException,LocalWorkerError,ValueError,
                        OSError,subprocess.SubprocessError) as error:
                    print("Kaurivo: yhteys tilapäisesti poikki. Työ ja tarkistuspisteet säilyvät.",
                          flush=True)
                    time.sleep(5)
        except KeyboardInterrupt:
            return 0
        finally:
            keep_running.clear()
            thread.join(timeout=2)
            listener.join(timeout=2)
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except LocalWorkerError as exc:
        print("Kaurivo Windows-rakentaja: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
