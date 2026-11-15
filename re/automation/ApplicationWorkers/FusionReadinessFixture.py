import json
import os
import queue
import runpy
import subprocess
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace

from ApplicationProtocol import (
    BOOTSTRAP,
    FUSION_PROVIDER,
    PROTOCOL,
    RESTART_GRANT,
    committed_bytes,
    configuration,
    encoded,
    file_bytes,
    identity,
    owner_lock,
    record,
    sha256,
    write_new,
)
from FusionRestartGrant import MAILBOX
from FusionRestartReadiness import request_response

ROOT = Path(__file__).resolve().parents[3]
BUILD = "fixture Fusion build"


class IdleEventSource:
    version = BUILD

    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.handler = None

    @property
    def documents(self):
        return SimpleNamespace(count=int((self.root / "document-open").exists()))

    @property
    def activeDocument(self):
        return object() if self.documents.count else None

    def registerCustomEvent(self, event):
        return self

    def unregisterCustomEvent(self, event):
        pass

    def add(self, handler):
        self.handler = handler

    def fireCustomEvent(self, event, payload):
        self.events.put(payload)
        return True

    def deliver(self):
        try:
            payload = self.events.get(timeout=0.05)
        except queue.Empty:
            return
        self.handler.notify(SimpleNamespace(additionalInfo=payload))


def host(root):
    app = IdleEventSource(root)
    adsk = ModuleType("adsk")
    core = ModuleType("adsk.core")
    core.Application = SimpleNamespace(get=lambda: app)
    core.CustomEventHandler = object
    adsk.core = core
    sys.modules.update(adsk=adsk, **{"adsk.core": core})
    bootstrap = runpy.run_path(str(ROOT / BOOTSTRAP))
    runtime = bootstrap["run"].__globals__
    runtime.update(HOME=root, QUEUE=root / "Legacy", IDLE_SECONDS=0.025)
    bootstrap["run"]({})
    queue_host = runtime["state"]["dispatch"]
    write_new(root / "ready.json", encoded(queue_host.host))
    try:
        while not (root / "stop").exists():
            app.deliver()
    finally:
        bootstrap["stop"]({})


def setup(root):
    endpoint = root / "Endpoint"
    endpoint.mkdir(mode=0o700)
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    path = root / "Installation.json"
    write_new(
        path,
        encoded(
            {
                "version": 1,
                "installation": "fixture:restart",
                "application": "fusion",
                "endpoint": str(endpoint),
                "source_root": str(ROOT),
                "source_revision": revision,
            }
        ),
    )
    write_new(
        root / "config.json",
        encoded(
            {
                "allowed_root": str(ROOT / "re/automation/PairedCaptures"),
                "dispatch": str(path),
            }
        ),
    )
    return path, endpoint


def ready(root, process):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and process.poll() is None:
        try:
            return record(root / "ready.json")
        except FileNotFoundError:
            time.sleep(0.025)
    raise RuntimeError("disposable Fusion callback did not start")


def stage(endpoint, installation, owner):
    config = configuration(installation)
    handoff = {
        "installation": config["installation"],
        "job_id": "a" * 32,
        "reason": "restart_required",
        "host": owner,
        "plan_sha256": "f" * 64,
        "at": time.time(),
        "owner": "external_application_owner",
    }
    fence = encoded(handoff)
    intent = encoded(
        {
            "version": 1,
            "provider": FUSION_PROVIDER,
            "installation": config["installation"],
            "installation_sha256": sha256(file_bytes(installation)),
            "source_revision": config["source_revision"],
            "protocol_sha256": sha256(committed_bytes(config, PROTOCOL)),
            "bootstrap_sha256": sha256(committed_bytes(config, BOOTSTRAP)),
            "fence_sha256": sha256(fence),
            "restart_handoff": handoff,
            "fusion_version": BUILD,
        }
    )
    write_new(endpoint / "fence.json", fence)
    write_new(endpoint / f"restart-intent-{handoff['job_id']}.json", intent)
    with owner_lock(endpoint / "dispatch.lock"):
        pass
    mailbox = endpoint / MAILBOX / "attempt-fixture"
    mailbox.parent.mkdir(mode=0o700)
    mailbox.mkdir(mode=0o700)
    request = {
        "version": 1,
        "operation": "issue",
        "installation": config["installation"],
        "source_revision": config["source_revision"],
        "handoff_id": handoff["job_id"],
        "challenge": "b" * 48,
        "intent_sha256": sha256(intent),
        "client": identity(os.getpid()),
        "deadline": time.time() + 10,
    }
    return mailbox, request, fence, sha256(committed_bytes(config, RESTART_GRANT))


def exercise(root, case):
    installation, endpoint = setup(root)
    process = subprocess.Popen(
        [sys.executable, "-B", __file__, str(root), "host"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        owner = ready(root, process)
        mailbox, request, fence, source = stage(endpoint, installation, owner)
        if case == "open":
            (root / "document-open").touch()
        if case == "changed-fence":
            fence = encoded({**json.loads(fence), "plan_sha256": "e" * 64})
            (endpoint / "fence.json").write_bytes(fence)
        if case == "expired":
            request["deadline"] = time.time() + 2
        lock = (
            nullcontext()
            if case == "unlocked"
            else owner_lock(endpoint / "dispatch.lock")
        )
        with lock:
            try:
                issued, grant_hash = request_response(mailbox, request, owner, source)
                if case == "opened-later":
                    (root / "document-open").touch()
                if case == "expired":
                    time.sleep(max(0, issued["expires_at"] - time.time()) + 0.1)
                followup = {
                    **request,
                    "operation": "consume",
                    "grant_sha256": grant_hash,
                    "deadline": (
                        issued["expires_at"] if case != "expired" else time.time() + 4
                    ),
                }
                result, _ = request_response(mailbox, followup, owner, source)
            except ValueError:
                operation = (
                    "issue"
                    if case in ("open", "unlocked", "changed-fence")
                    else "consume"
                )
                reply = record(mailbox / f"{operation}.response")
                assert reply["status"] == "refused"
                assert not (mailbox / "issue.consumed").exists()
                result = reply
            else:
                assert case == "accepted"
                assert sha256(file_bytes(mailbox / "issue.consumed")) == grant_hash
                assert not (mailbox / "issue.response").exists()
                try:
                    request_response(mailbox, followup, owner, source)
                except ValueError:
                    assert sha256(file_bytes(mailbox / "issue.consumed")) == grant_hash
                else:
                    raise AssertionError("consumed grant was replayed")
        assert file_bytes(endpoint / "fence.json") == fence
        assert not any((endpoint / "jobs").iterdir()) and process.poll() is None
        print(
            json.dumps(
                {"status": result["status"], "host": result["host"], "case": case}
            )
        )
    finally:
        (root / "stop").touch()
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stdout + stderr


if __name__ == "__main__":
    root = Path(sys.argv[1])
    case = sys.argv[2]
    if case == "host":
        host(root)
    else:
        exercise(root, case)
