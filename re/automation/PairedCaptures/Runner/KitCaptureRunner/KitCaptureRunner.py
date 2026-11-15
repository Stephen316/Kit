import json
import os
import runpy
import re
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import adsk.core


def runner_home():
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData/Roaming") / "KitCaptureRunner"
    return Path.home() / "Library/Application Support/KitCaptureRunner"


HOME = runner_home()
BOOTSTRAP_SOURCE = Path(__file__).read_bytes()
QUEUE = HOME / "queue"
EVENT_ID = "KitCaptureRunnerJob"
SCRIPT_NAME = "GenerateFusion.py"
IDLE_SECONDS = 2.0

state = {
    "app": None, "event": None, "handlers": [], "stop": threading.Event(), "finished": threading.Event(),
    "thread": None, "started_utc": None, "busy_seconds": 0.0, "jobs": 0, "failed": 0,
    "dispatch": None, "dispatch_protocol": None, "restart_grant": None,
    "main_thread": None, "active_callback": False,
}


def allowed_root():
    config = json.loads((HOME / "config.json").read_text(encoding="utf-8"))
    return Path(config["allowed_root"]).resolve(strict=True)


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_status(status):
    elapsed = max(time.time() - state["started_utc"], 1e-9) if state["started_utc"] else None
    write_json(HOME / "runner.json", {
        "status": status, "pid": os.getpid(), "fusion_version": state["app"].version if state["app"] else None,
        "started_utc": state["started_utc"], "updated_utc": time.time(), "jobs": state["jobs"], "failed": state["failed"],
        "busy_seconds": round(state["busy_seconds"], 3),
        "utilization": round(state["busy_seconds"] / elapsed, 4) if elapsed else None,
    })


def run_job(job_path):
    if job_path.suffix == ".request":
        protocol = state["dispatch_protocol"]
        host = state["dispatch"]
        counterpart = protocol["load_pinned"](host.config, protocol["COUNTERPART"])
        counterpart["protocol"] = protocol
        counterpart["serve"](host, job_path, state["app"])
        return
    running = job_path.with_suffix(".running")
    os.replace(job_path, running)
    started = time.time()
    status = {"job": job_path.name, "started_utc": started, "fusion_version": state["app"].version}
    try:
        job = json.loads(running.read_text(encoding="utf-8"))
        script = Path(job["script"]).resolve(strict=True)
        if script.name != SCRIPT_NAME or script.parent.parent != allowed_root():
            raise ValueError("script is outside the configured capture folder")
        status["script"] = str(script)
        namespace = runpy.run_path(str(script), run_name="kit_capture")
        namespace["run"]({})
        status["status"] = "finished"
    except Exception:
        status["status"] = "failed"
        status["error"] = traceback.format_exc()
    status["ended_utc"] = time.time()
    write_json(running.with_suffix(".done"), status)
    running.unlink()
    state["busy_seconds"] += status["ended_utc"] - started
    state["jobs"] += 1
    state["failed"] += status["status"] == "failed"
    write_status("running")


class JobHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        if state["active_callback"]:
            return
        state["active_callback"] = True
        try:
            request = json.loads(args.additionalInfo)
            if set(request) == {"restart"}:
                grant = state["restart_grant"]
                grant["serve"](
                    state["dispatch_protocol"], grant["_source_pin"], state["dispatch"],
                    Path(request["restart"]), state["app"], state["main_thread"],
                )
            else:
                run_job(Path(request["job"]))
        except Exception:
            write_json(HOME / "runner-error.json", {"error": traceback.format_exc(), "time_utc": time.time()})
        finally:
            state["active_callback"] = False
            state["finished"].set()


def poll():
    stop = state["stop"]
    while not stop.is_set():
        host = state["dispatch"]
        grant = state["restart_grant"]
        readiness = grant["pending_request"](state["dispatch_protocol"], host) if host is not None else None
        if readiness is not None:
            request = {"restart": str(readiness)}
        else:
            request_path = host.next_path() if host is not None else None
            jobs = [request_path] if request_path is not None else sorted(QUEUE.glob("*.json")) if host is None or host.legacy_available() else []
            if not jobs:
                stop.wait(IDLE_SECONDS)
                continue
            request = {"job": str(jobs[0])}
        state["finished"].clear()
        if not state["app"].fireCustomEvent(EVENT_ID, json.dumps(request)):
            stop.wait(IDLE_SECONDS)
            continue
        while not stop.is_set() and not state["finished"].wait(0.5):
            pass


def run(context):
    app = adsk.core.Application.get()
    state["app"] = app
    state["main_thread"] = threading.get_ident()
    QUEUE.mkdir(parents=True, exist_ok=True)
    allowed_root()
    config = json.loads((HOME / "config.json").read_text(encoding="utf-8"))
    if "dispatch" in config:
        installation = json.loads(Path(config["dispatch"]).read_bytes())
        root = allowed_root().parents[2]
        if not re.fullmatch("[0-9a-f]{40}", installation["source_revision"]) or Path(installation["source_root"]).resolve() != root:
            raise ValueError("dispatch installation must pin this configured repository")
        relative = "re/automation/ApplicationWorkers/ApplicationProtocol.py"
        path = root / relative
        source = subprocess.run(["git", "-C", str(root), "show", f"{installation['source_revision']}:{relative}"], capture_output=True, check=False, timeout=15)
        if source.returncode != 0 or path.is_symlink() or path.read_bytes() != source.stdout or len(source.stdout) > 1024 * 1024:
            raise ValueError("application protocol differs from its pinned revision")
        protocol = {"__name__": "__kit_pinned_queue__", "__file__": str(path)}
        exec(compile(source.stdout, str(path), "exec"), protocol)
        installation_bytes = protocol["file_bytes"](config["dispatch"])
        checked_installation = protocol["validate_configuration"](json.loads(installation_bytes))
        if checked_installation != installation:
            raise ValueError("dispatch installation changed during add-in startup")
        installation = checked_installation
        if sys.platform != "darwin" or installation["application"] != "fusion":
            raise ValueError("fresh-phase dispatch currently requires a macOS Fusion host")
        trusted_bootstrap = protocol["committed_bytes"](installation, protocol["BOOTSTRAP"])
        if BOOTSTRAP_SOURCE != trusted_bootstrap:
            raise ValueError("reload the add-in from the trusted installation revision")
        state["restart_grant"] = protocol["load_pinned"](installation, protocol["RESTART_GRANT"])
        state["dispatch_protocol"] = protocol
        state["dispatch"] = protocol["HostQueue"](installation)
        state["dispatch"].installation_sha256 = protocol["sha256"](installation_bytes)
        state["dispatch"].loaded_sources = {
            "bootstrap": {"path": protocol["BOOTSTRAP"], "sha256": protocol["sha256"](BOOTSTRAP_SOURCE), "size_bytes": len(BOOTSTRAP_SOURCE), "revision": installation["source_revision"]},
            "protocol": {"path": relative, "sha256": protocol["sha256"](source.stdout), "size_bytes": len(source.stdout), "revision": installation["source_revision"]},
        }
    event = app.registerCustomEvent(EVENT_ID)
    handler = JobHandler()
    event.add(handler)
    state["event"], state["handlers"] = event, [handler]
    state["stop"].clear()
    state["started_utc"] = time.time()
    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    state["thread"] = thread
    write_status("running")


def stop(context):
    state["stop"].set()
    if state["app"] is not None:
        state["app"].unregisterCustomEvent(EVENT_ID)
    if state["dispatch"] is not None:
        state["dispatch"].close()
        state["dispatch"] = None
    write_status("stopped")
