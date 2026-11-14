import json
import os
import runpy
import threading
import time
import traceback
from pathlib import Path

import adsk.core

HOME = Path.home() / "Library/Application Support/KitCaptureRunner"
QUEUE = HOME / "queue"
EVENT_ID = "KitCaptureRunnerJob"
SCRIPT_NAME = "GenerateFusion.py"

state = {"app": None, "event": None, "handlers": [], "stop": threading.Event(), "thread": None}


def allowed_root():
    config = json.loads((HOME / "config.json").read_text(encoding="utf-8"))
    return Path(config["allowed_root"]).resolve(strict=True)


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run_job(job_path):
    running = job_path.with_suffix(".running")
    os.replace(job_path, running)
    status = {"job": job_path.name, "started_utc": time.time(), "fusion_version": state["app"].version}
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


class JobHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        try:
            run_job(Path(json.loads(args.additionalInfo)["job"]))
        except Exception:
            write_json(HOME / "runner-error.json", {"error": traceback.format_exc(), "time_utc": time.time()})


def poll():
    stop = state["stop"]
    while not stop.wait(2.0):
        jobs = sorted(QUEUE.glob("*.json"))
        if not jobs:
            continue
        job = jobs[0]
        state["app"].fireCustomEvent(EVENT_ID, json.dumps({"job": str(job)}))
        while not stop.is_set() and (job.exists() or job.with_suffix(".running").exists()):
            stop.wait(0.5)


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
    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    state["thread"] = thread
    write_json(HOME / "runner.json", {"status": "running", "pid": os.getpid(), "fusion_version": app.version, "started_utc": time.time()})


def stop(context):
    state["stop"].set()
    if state["app"] is not None:
        state["app"].unregisterCustomEvent(EVENT_ID)
    write_json(HOME / "runner.json", {"status": "stopped", "stopped_utc": time.time()})
