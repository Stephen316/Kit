import json
import os
import runpy
import re
import stat
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


# candidate paths cannot redirect early startup outside the provisioned local volume
def startup_path(path, *, file=False, single_link=True):
    path = Path(path)
    if not path.is_absolute() or path.anchor.startswith("\\\\"):
        raise ValueError("Windows add-in startup requires absolute local paths")
    for ancestor in (*reversed(path.parents), path):
        info = ancestor.lstat()
        regular = file and ancestor == path
        expected = stat.S_ISREG(info.st_mode) if regular else stat.S_ISDIR(info.st_mode)
        if regular and single_link:
            expected = expected and info.st_nlink == 1
        if not expected or info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("Windows add-in startup paths must be regular and free of links")
    return path


# startup needs bounded candidate records before it has an approved record reader
def startup_record(path):
    with startup_path(path, file=True).open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("add-in startup record exceeds 1 MiB")
    return raw


# an implicit working directory must never supply executable source authority
def startup_git():
    for entry in os.get_exec_path():
        candidate = Path(entry.strip('"')) / "git.exe"
        if candidate.is_absolute() and not candidate.anchor.startswith("\\\\") and candidate.is_file():
            return str(startup_path(candidate, file=True, single_link=False))
    raise ValueError("Windows add-in startup requires trusted Git on an absolute PATH entry")


# the installed addin may only execute helpers from its configured git checkout
def windows_sources(config, installation):
    allowed = startup_path(config["allowed_root"])
    root = allowed.resolve(strict=True).parents[2]
    revision = installation["source_revision"]
    source_root = startup_path(installation["source_root"])
    if not re.fullmatch("[0-9a-f]{40}", revision) or source_root.resolve(strict=True) != root:
        raise ValueError("dispatch installation must pin this configured repository")
    git_executable = startup_git()
    git = [git_executable, "--no-replace-objects", "-C", str(root)]
    checkout = subprocess.check_output([*git, "rev-parse", "--show-toplevel"], timeout=15)
    commit = subprocess.check_output([*git, "rev-parse", "--verify", f"{revision}^{{commit}}"], timeout=15)
    if Path(os.fsdecode(checkout.strip())).resolve(strict=True) != root or commit.strip() != revision.encode():
        raise ValueError("dispatch installation must pin a commit in this configured checkout")
    paths = {
        "bootstrap": "re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py",
        "protocol": "re/automation/ApplicationWorkers/ApplicationProtocol.py",
        "windows_identity": "re/automation/ApplicationWorkers/WindowsIdentity.py",
        "windows_records": "re/automation/ApplicationWorkers/WindowsRecords.py",
    }
    sources = {}
    for role, relative in paths.items():
        raw = subprocess.check_output([*git, "show", f"{revision}:{relative}"], timeout=15)
        if not 0 < len(raw) <= 1024 * 1024:
            raise ValueError("pinned add-in source is outside its byte limit")
        sources[role] = (relative, raw)
    if BOOTSTRAP_SOURCE != sources["bootstrap"][1]:
        raise ValueError("reload the add-in from the trusted installation revision")
    return root, sources, git_executable


# the embedded interpreter has no trusted sibling import path for dispatch helpers
def start_windows_dispatch(config_path, config_bytes):
    config = json.loads(config_bytes)
    installation_path = Path(config["dispatch"])
    if not installation_path.is_absolute():
        raise ValueError("dispatch installation path must be absolute")
    installation_bytes = startup_record(installation_path)
    installation = json.loads(installation_bytes)
    if installation.get("windows_phase_a") is not True or installation.get("application") != "fusion":
        raise ValueError("Windows Fusion Phase A requires owner opt-in")
    startup_path(__file__, file=True)
    endpoint = startup_path(installation["endpoint"])
    root, sources, git_executable = windows_sources(config, installation)
    scopes = {}
    for role in ("windows_identity", "windows_records", "protocol"):
        relative, raw = sources[role]
        path = str(root / relative)
        scope = {"__name__": f"__kit_pinned_{role}__", "__file__": path}
        exec(compile(raw, path, "exec"), scope)
        scopes[role] = scope
    protocol = scopes["protocol"]
    protocol["WINDOWS_GIT"] = git_executable
    protocol["WINDOWS_API"].update({
        "windows_identity": {name: scopes["windows_identity"][name] for name in ("process_start", "peer_matches")},
        "windows_records": {name: scopes["windows_records"][name] for name in ("open_record", "open_owner_lock")},
    })
    file_bytes = protocol["file_bytes"]
    if file_bytes(config_path) != config_bytes or file_bytes(installation_path) != installation_bytes:
        raise ValueError("dispatch startup records changed during add-in loading")
    installation = protocol["validate_configuration"](installation)
    protocol["directory"](config["allowed_root"])
    protocol["directory"](installation["source_root"])
    protocol["directory"](endpoint)
    if file_bytes(__file__) != BOOTSTRAP_SOURCE:
        raise ValueError("installed add-in changed during dispatch startup")
    for relative, raw in sources.values():
        if file_bytes(root / relative) != raw:
            raise ValueError(f"application source differs from its pinned revision: {relative}")
    host = protocol["HostQueue"](installation)
    host.loaded_sources = {
        role: protocol["source_pin"](installation, relative, raw)
        for role, (relative, raw) in sources.items()
    }
    state.update(dispatch=host, dispatch_protocol=protocol, restart_grant=None)


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
        if protocol["windows_phase_a"](host.config) and threading.get_ident() != state["main_thread"]:
            raise ValueError("Windows Fusion capture requires the add-in main thread")
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
        readiness = grant["pending_request"](state["dispatch_protocol"], host) if grant is not None and host is not None else None
        if readiness is not None:
            request = {"restart": str(readiness)}
        else:
            request_path = host.next_path() if host is not None else None
            if request_path is not None:
                jobs = [request_path]
            else:
                legacy = host is None or (sys.platform != "win32" and host.legacy_available())
                jobs = sorted(QUEUE.glob("*.json")) if legacy else []
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
    config_path = HOME / "config.json"
    if sys.platform == "win32":
        config_bytes = startup_record(config_path)
        config = json.loads(config_bytes)
        if "dispatch" in config:
            start_windows_dispatch(config_path, config_bytes)
        else:
            allowed_root()
            QUEUE.mkdir(parents=True, exist_ok=True)
    else:
        QUEUE.mkdir(parents=True, exist_ok=True)
        allowed_root()
        config = json.loads(config_path.read_text(encoding="utf-8"))
    if sys.platform != "win32" and "dispatch" in config:
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
    state["app"] = app
    state["main_thread"] = threading.get_ident()
    try:
        event = app.registerCustomEvent(EVENT_ID)
        handler = JobHandler()
        event.add(handler)
    except BaseException:
        if sys.platform == "win32" and state["dispatch"] is not None:
            state["dispatch"].close()
            state["dispatch"] = None
        raise
    state["event"], state["handlers"] = event, [handler]
    state["stop"].clear()
    state["started_utc"] = time.time()
    thread = threading.Thread(target=poll, daemon=True)
    thread.start()
    state["thread"] = thread
    write_status("running")


def stop(context):
    if sys.platform == "win32" and state["started_utc"] is None:
        return
    state["stop"].set()
    if state["app"] is not None:
        state["app"].unregisterCustomEvent(EVENT_ID)
    if state["dispatch"] is not None:
        state["dispatch"].close()
        state["dispatch"] = None
    write_status("stopped")
    if sys.platform == "win32":
        state["started_utc"] = None
