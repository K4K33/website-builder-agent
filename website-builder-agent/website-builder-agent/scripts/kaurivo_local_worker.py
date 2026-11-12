"""Owner-enrolled, free-only Windows demo builder.

Polls the authenticated Kaurivo private queue once per second while ready.
No GitHub Actions, service-role token, browser session, paid AI or webhook
needed to *start*. Uses exactly the existing source/brand/QA pipeline.
"""
from __future__ import annotations

import json
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
POLL_SECONDS=1.0
PING_SECONDS=10.0


class LocalWorkerError(RuntimeError):
    pass


def models() -> dict[str,str]:
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
        env=os.environ.copy()
        env.update({
           "KAURIVO_LOCAL_WORKER":"1",
           "KAURIVO_LOCAL_WORKER_TOKEN":token,
           "KAURIVO_CLAIMED_JOB_FILE":str(claim),
           "RUNNER_TEMP":tmp,"GITHUB_RUN_ID":str(run_id),
           "FREE_ONLY":"1","AI_BACKEND":"ollama",
           "RESEARCH_AI_BACKEND":"ollama",
           "BUILDER_AI_BACKEND":"ollama",
           "QA_AI_BACKEND":"ollama",
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


def main() -> int:
    token=os.environ.get("KAURIVO_LOCAL_WORKER_TOKEN","").strip()
    if not TOKEN_RE.fullmatch(token):
        raise LocalWorkerError("Windows setup token missing or invalid.")
    model_names=models()
    file=singleton_lock()
    with file,requests.Session() as session:
        print("Kaurivo Windows-rakentaja käynnissä. Painallus tarkistetaan noin sekunnissa.",
              flush=True)
        last_ping=0.0
        worker_id=None
        ready_before=None
        pending=None
        keep_running=threading.Event()
        keep_running.set()
        # Do not leave a long local inference without a heartbeat: GitHub's
        # stale-job sweeper may otherwise recycle the same claimed company.
        def heartbeat():
            while keep_running.is_set():
                try:server(session,token,"ping",ready=ollama_ready(session,model_names))
                except (requests.RequestException,LocalWorkerError,ValueError):
                    pass
                keep_running.wait(10)  # wake on shutdown, no busy-loop
        # Avoid thread safety issues on requests.Session: heartbeat owns its
        # own Session object. Caller reuses the main session.
        def safe_heartbeat():
            with requests.Session() as ping_session:
                while keep_running.is_set():
                    try:server(ping_session,token,"ping",
                               ready=ollama_ready(ping_session,model_names))
                    except (requests.RequestException,LocalWorkerError,ValueError):
                        pass
                    # Event.wait(true) would spin, so use shutdown-aware sleep.
                    for _ in range(10):
                        if not keep_running.is_set():break
                        time.sleep(1)
        thread=threading.Thread(target=safe_heartbeat,daemon=True)
        thread.start()
        try:
            while True:
                ready=ollama_ready(session,model_names)
                if ready!=ready_before:
                    print("Kaurivo local AI "+("valmis" if ready else "ei vielä valmis")+
                          " (kaikki mallit oltava asennettuna; QA-mallilla näkökyky).",
                          flush=True)
                    ready_before=ready
                if not ready:
                    time.sleep(5)
                    continue
                try:
                    data=server(session,token,"claim")
                    job=data.get("job")
                    if job:
                        worker_id=int(data["run_id"])
                        print("Kaurivo aloittaa valitun yrityksen rakennustyön.",flush=True)
                        run_claim(job,worker_id,token,model_names)
                    else:
                        time.sleep(POLL_SECONDS)
                except (requests.RequestException,LocalWorkerError,ValueError) as error:
                    print("Kaurivo: yhteys tilapäisesti poikki. Työ ja tarkistuspisteet säilyvät.",
                          flush=True)
                    time.sleep(5)
        except KeyboardInterrupt:
            return 0
        finally:
            keep_running.clear()
            thread.join(timeout=2)
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except LocalWorkerError as exc:
        print("Kaurivo Windows-rakentaja: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
