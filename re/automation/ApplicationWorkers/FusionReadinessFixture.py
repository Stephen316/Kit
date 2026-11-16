import json
import os
import queue
import runpy
import subprocess
import sys
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace

import ApplicationProtocol as protocol
from ApplicationProtocol import (
    BOOTSTRAP,
    FUSION_PROVIDER,
    MAC_COCOA_QUIT,
    MAC_QUIT_AUTHORIZATION,
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
from FusionExitEvidence import seal_and_watch
from FusionExitRecords import exit_evidence
from FusionQuitAuthorization import authorize, paths
from FusionQuitRelease import bind_replacement
from FusionRestartGrant import MAILBOX
from FusionRestartReadiness import request_response
from MacApplicationPeer import process_peer

ROOT = Path(__file__).resolve().parents[3]
BUILD = "fixture Fusion build"


class IdleEventSource:
    version = BUILD
    isStartupComplete = True
    hasActiveJobs = False

    def __init__(self, root, case):
        self.root = root
        self.case = case
        self.events = queue.Queue()
        self.handler = None

    @property
    def documents(self):
        opened = (self.root / "document-open").exists()
        if self.case == "auto-after-reserve":
            opened |= any((self.root / "Endpoint").glob("quit-attempt-*.json"))
        return SimpleNamespace(count=int(opened))

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
        request = json.loads(payload)
        if (
            Path(request.get("restart", "")).name.startswith("quit-request-")
            and (self.root / "pause-quit").exists()
        ):
            self.events.put(payload)
            time.sleep(0.025)
            return
        self.handler.notify(SimpleNamespace(additionalInfo=payload))


def host(root, case):
    app = IdleEventSource(root, case)
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
    state = runtime["state"]
    queue_host = state["dispatch"]
    if case.startswith("auto-"):

        def quit_fixture():
            write_new(root / "invoked.json", encoded({"pid": os.getpid()}))
            if case == "auto-exit":
                os._exit(0)
            if case == "auto-uncertain":
                time.sleep(3)

        state["restart_grant"]["_automatic_quit"]["bridge"][
            "request_quit"
        ] = quit_fixture
    elif case == "replacement":
        original_gate = queue_host.mac_quit_replacement

        def consulted_gate(fence):
            allowed = original_gate(fence)
            blocked = root / "replacement-blocked.json"
            if not allowed and not blocked.exists():
                write_new(blocked, encoded(queue_host.host))
            return allowed

        queue_host.mac_quit_replacement = consulted_gate
    name = "replacement-ready.json" if case == "replacement" else "ready.json"
    write_new(root / name, encoded(queue_host.host))
    try:
        while not (root / "stop").exists():
            app.deliver()
    finally:
        bootstrap["stop"]({})


def setup(root, *, automatic=False):
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
                **({"macos_automatic_quit": True} if automatic else {}),
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


def ready(root, process, name="ready.json"):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and process.poll() is None:
        try:
            return record(root / name)
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


def consume_readiness(mailbox, request, owner, source, installation):
    first, grant_hash = request_response(mailbox, request, owner, source)
    final, final_hash = request_response(
        mailbox,
        {
            **request,
            "operation": "consume",
            "grant_sha256": grant_hash,
            "deadline": first["expires_at"],
        },
        owner,
        source,
    )
    peer = process_peer(owner["pid"])
    return {
        "version": 1,
        "status": "restart_readiness_observed",
        "documents": 0,
        "peer": {key: value for key, value in peer.items() if key != "executable"},
        "intent_sha256": request["intent_sha256"],
        "installation_sha256": sha256(file_bytes(installation)),
        "provider_source_sha256": source,
        "observed_at": final["observed_at"],
        "expires_at": first["expires_at"],
        "grant_sha256": grant_hash,
        "consumption_sha256": final_hash,
        "grant": first,
        "consumption": final,
    }, peer["executable"]


def prove_replacement_gate(
    root, endpoint, readiness, executable, handoff, result, fence
):
    identifier = result["quit_intent_sha256"]
    release = {
        "version": 1,
        "scope": "owner_fusion_replacement_request",
        "handoff_id": handoff,
        "restart_intent_sha256": readiness["intent_sha256"],
        "installation_sha256": readiness["installation_sha256"],
        "fence_sha256": sha256(fence),
        "quit_intent_sha256": identifier,
        "quit_exit_sha256": result["receipt_sha256"],
        "requested_at": time.time(),
    }
    raw = encoded(release)
    write_new(endpoint / f"replacement-launch-{identifier}.json", raw)
    bind_replacement(vars(protocol), endpoint, release, sha256(raw), executable)
    dispatched_at = time.time()
    process = subprocess.Popen(
        [sys.executable, "-B", __file__, str(root), "host", "replacement"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        owner = ready(root, process, "replacement-ready.json")
        assert ready(root, process, "replacement-blocked.json") == owner
        peer = process_peer(owner["pid"])
        assert (
            peer["pid"] != readiness["peer"]["pid"] and peer["executable"] == executable
        )
        assert file_bytes(endpoint / "fence.json") == fence
        receipt = {
            "version": 1,
            "scope": "owner_fusion_replacement_observation",
            "status": "replacement_process_observed",
            "launch_request_sha256": sha256(raw),
            "quit_intent_sha256": identifier,
            "quit_exit_sha256": result["receipt_sha256"],
            "dispatched_at": dispatched_at,
            "host": owner,
            "peer": {key: value for key, value in peer.items() if key != "executable"},
        }
        write_new(endpoint / f"replacement-peer-{identifier}.json", encoded(receipt))
        deadline = time.monotonic() + 7
        while (endpoint / "fence.json").exists() and time.monotonic() < deadline:
            assert process.poll() is None
            time.sleep(0.025)
        assert not (endpoint / "fence.json").exists()
    finally:
        (root / "stop").touch()
        stdout, stderr = process.communicate(timeout=10)
        assert process.returncode == 0, stdout + stderr


def verify_automatic(root, process, installation, endpoint, case):
    owner = ready(root, process)
    mailbox, request, fence, source = stage(endpoint, installation, owner)
    config = configuration(installation)
    bridge_sha = sha256(committed_bytes(config, MAC_COCOA_QUIT))
    action_sha = sha256(committed_bytes(config, MAC_QUIT_AUTHORIZATION))
    files = paths(endpoint, request["intent_sha256"])
    pause = root / "pause-quit"
    fence_path = endpoint / "fence.json"
    changed_fence = encoded({**json.loads(fence), "plan_sha256": "e" * 64})
    with owner_lock(endpoint / "dispatch.lock"):
        readiness, executable = consume_readiness(
            mailbox, request, owner, source, installation
        )

        def verify():
            assert file_bytes(fence_path) == fence

        @contextmanager
        def publish(identifier, deadline):
            with authorize(
                vars(protocol),
                config,
                endpoint,
                readiness,
                executable,
                identifier,
                deadline,
                process_peer,
                bridge_sha,
                action_sha,
            ) as read_action:
                if case == "auto-fence":
                    fence_path.write_bytes(changed_fence)
                    pause.unlink()
                yield read_action

        def armed(identifier):
            assert not files["request"].exists()
            assert (endpoint / f"quit-intent-{identifier}.json").is_file()
            if case == "auto-open":
                (root / "document-open").touch()

        try:
            with publish("0" * 64, time.monotonic_ns() + 1_000_000_000):
                raise AssertionError("quit request published without an armed intent")
        except FileNotFoundError:
            assert not files["request"].exists()
        if case in ("auto-expired", "auto-fence"):
            pause.touch()
        result = seal_and_watch(
            endpoint,
            readiness,
            executable,
            sha256(fence),
            8 if case == "auto-exit" else 2,
            verify,
            armed,
            authorize=publish,
        )
        if pause.exists():
            pause.unlink()
            deadline = time.monotonic() + 5
            while not files["action"].exists() and time.monotonic() < deadline:
                time.sleep(0.025)
            assert record(files["action"])["status"] == "refused"
        if case == "auto-cancel":
            initial = file_bytes(files["attempt"])
            try:
                seal_and_watch(
                    endpoint,
                    readiness,
                    executable,
                    sha256(fence),
                    2,
                    verify,
                    lambda _: None,
                    authorize=publish,
                )
            except FileExistsError:
                assert file_bytes(files["attempt"]) == initial
            else:
                raise AssertionError(
                    "accepted restart intent allowed another quit request"
                )
        if case == "auto-exit":
            assert process.wait(timeout=5) == 0
            _, receipt = exit_evidence(
                endpoint, result["quit_intent_sha256"], result["receipt_sha256"]
            )
            assert receipt["cause"] == "unverified"
            assert not files["action"].exists()
        else:
            assert process.poll() is None and not list(
                endpoint.glob("quit-exit-*.json")
            )
        if case == "auto-after-reserve":
            assert files["attempt"].is_file()
    assert file_bytes(fence_path) == (changed_fence if case == "auto-fence" else fence)
    if case == "auto-exit":
        prove_replacement_gate(
            root, endpoint, readiness, executable, request["handoff_id"], result, fence
        )
    called = (root / "invoked.json").is_file()
    assert called is (case in ("auto-exit", "auto-cancel", "auto-uncertain"))
    print(json.dumps({**result, "case": case, "called": called}))


def exercise(root, case):
    automatic = case.startswith("auto-")
    installation, endpoint = setup(root, automatic=automatic)
    process = subprocess.Popen(
        [sys.executable, "-B", __file__, str(root), "host", case],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        if automatic:
            verify_automatic(root, process, installation, endpoint, case)
            return
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
        host(root, sys.argv[3])
    else:
        exercise(root, case)
