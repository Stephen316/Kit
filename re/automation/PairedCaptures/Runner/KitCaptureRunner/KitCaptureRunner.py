import json
import os
import runpy
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
QUEUE = HOME / "queue"
EVENT_ID = "KitCaptureRunnerJob"
SCRIPT_NAME = "GenerateFusion.py"
IDLE_SECONDS = 2.0

state = {
    "app": None, "event": None, "handlers": [], "stop": threading.Event(), "finished": threading.Event(),
    "thread": None, "started_utc": None, "busy_seconds": 0.0, "jobs": 0, "failed": 0,
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
        try:
            run_job(Path(json.loads(args.additionalInfo)["job"]))
        except Exception:
            write_json(HOME / "runner-error.json", {"error": traceback.format_exc(), "time_utc": time.time()})
        finally:
            state["finished"].set()


def poll():
    stop = state["stop"]
    while not stop.is_set():
        jobs = sorted(QUEUE.glob("*.json"))
        if not jobs:
            stop.wait(IDLE_SECONDS)
            continue
        state["finished"].clear()
        state["app"].fireCustomEvent(EVENT_ID, json.dumps({"job": str(jobs[0])}))
        while not stop.is_set() and not state["finished"].wait(0.5):
            pass


def run(context):
    app = adsk.core.Application.get()
    state["app"] = app
    QUEUE.mkdir(parents=True, exist_ok=True)
    allowed_root()
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
    write_status("stopped")
