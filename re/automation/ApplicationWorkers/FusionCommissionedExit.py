import json
import os
import time
from contextlib import ExitStack

from ApplicationProtocol import encoded, file_bytes, require, sha256
from FusionExitRecords import exit_evidence, pin, read_pinned
from FusionLifecycleRecords import eligible_exit, optional
from FusionLifecycleRegistration import checked_policy
from FusionQueueReceipt import seal
from MacApplicationPeer import process_peer
from MacProcessExit import observe_exit, watch_peer

# only source reviewed for this observation can attest the commissioned process lifetime
WATCH_POLICY = (
    "ApplicationWorkers/FusionCommissionedExit.py",
    "ApplicationWorkers/FusionOwnerColdStart.py",
    "ApplicationWorkers/FusionStartupProvision.py",
    "ApplicationWorkers/MacApplicationPeer.py",
    "ApplicationWorkers/MacProcessExit.py",
)


# the continuing owner keeps one kernel watch for the exact commissioned initial peer
class CommissionedExit(ExitStack):
    def __init__(self, root):
        super().__init__()
        self.root = root
        self.target = None
        self.planned = None
        self.epoch = None

    def arm(self, boot, admission):
        epoch, executable = admitted_epoch(boot, admission)
        self.epoch = epoch
        digest = epoch["admission_sha256"]
        path = self.root / f"initial-native-exit-{digest}.json"
        existing = optional(path)
        if existing is not None:
            return self.report(validate_exit(self.root, epoch, existing), existing)
        peer = epoch["peer"]
        watcher = process_peer(os.getpid())
        with ExitStack() as custody:
            watcher_socket = custody.enter_context(watch_peer(peer, executable))
            intent = {
                "version": 1,
                "scope": "fusion_commissioned_native_exit_watch",
                "epoch": epoch,
                "armed_at": time.time(),
                "watcher": {
                    key: value for key, value in watcher.items() if key != "executable"
                },
            }
            raw = encoded(intent)
            checksum = sha256(raw)
            seal(self.root / f"initial-native-watch-{checksum}.json", raw)
            self.enter_context(custody.pop_all())
        self.target = (watcher_socket, intent, checksum, path)
        return {"status": "commissioned_exit_watch_armed", "watch_sha256": checksum}

    def collect(self):
        if self.target is None:
            return None
        monitor, intent, watch_sha, path = self.target
        epoch = intent["epoch"]
        try:
            event = observe_exit(monitor, epoch["peer"], 0)
        except (OSError, ValueError):
            self.target = None
            self.close()
            raise
        if event is None:
            return None
        self.target = None
        self.close()
        require(
            event["observed_at"] >= intent["armed_at"], "Fusion exit precedes watcher"
        )
        disposition = quit_disposition(self.root, self.planned, epoch)
        result = {
            "version": 1,
            "scope": "fusion_commissioned_native_exit",
            "watch_sha256": watch_sha,
            "epoch": epoch,
            **event,
            **disposition,
        }
        raw = encoded(result)
        seal(path, raw)
        return self.report(result, raw)

    def report(self, result, raw):
        return {
            "status": "commissioned_native_exit_observed",
            "exit_sha256": sha256(raw),
            "disposition": result["disposition"],
        }


# the admitted startup receipt ties the live kernel peer to the exact installation and job
def admitted_epoch(boot, admission):
    from FusionOwnerColdStart import PEER, REQUEST

    boot.verify_inputs()
    checksum = pin(admission["evidence_sha256"])
    request_path = boot.root / REQUEST
    request_raw = file_bytes(request_path)
    request = json.loads(request_raw)
    require(
        all(request[key] == value for key, value in boot.binding().items())
        and boot.recorded(request_raw, request) == admission,
        "commissioned Fusion watcher lacks the exact A03 admission",
    )
    checked_policy(boot.config, boot.queue["resource"], extra=WATCH_POLICY)
    proof = read_pinned(boot.root / f"cold-start-admission-{checksum}.json", checksum)
    launch = read_pinned(boot.root / PEER, proof["launch_receipt_sha256"])
    boot.verify_launch(request_raw, request, launch)
    require(
        proof["startup_receipt"]["peer"]
        == {**launch["peer"], "executable": os.fspath(boot.executable)}
        and proof["startup_receipt"]["source_revision"]
        == boot.config["source_revision"],
        "commissioned Fusion watcher lacks exact startup peer provenance",
    )
    return {
        "admission_sha256": checksum,
        "startup_sha256": proof["startup_receipt_sha256"],
        "launch_sha256": proof["launch_receipt_sha256"],
        "installation_sha256": request["installation_sha256"],
        "lifecycle_sha256": request["lifecycle_sha256"],
        "queue_receipt_sha256": request["queue_receipt_sha256"],
        "source_revision": request["source_revision"],
        "job": request["admission"]["phase_a"],
        "generation": request["admission"]["generation"],
        "fingerprint": request["admission"]["fingerprint"],
        "peer": launch["peer"],
    }, boot.executable


# an existing exit receipt must tie back to the saved watch and exact admitted peer
def validate_exit(root, epoch, raw):
    value = json.loads(raw)
    watch = pin(value["watch_sha256"])
    intent = read_pinned(root / f"initial-native-watch-{watch}.json", watch)
    require(
        value["version"] == intent["version"] == 1
        and intent["scope"] == "fusion_commissioned_native_exit_watch"
        and value["scope"] == "fusion_commissioned_native_exit"
        and value["epoch"] == intent["epoch"] == epoch
        and value["observation"] == "darwin_process_exit_event"
        and value["disposition"]
        in (
            "outside_owner_scheduled_quit",
            "scheduled_quit_observed",
            "scheduled_quit_unresolved",
        )
        and intent["armed_at"] <= value["observed_at"] <= time.time(),
        "commissioned Fusion exit lost its exact recorded watch",
    )
    if value["disposition"] == "scheduled_quit_observed":
        ready, _ = exit_evidence(
            root, value["scheduled_quit_intent_sha256"], value["scheduled_exit_sha256"]
        )
        require(
            same_peer(ready, epoch), "scheduled exit differs from the commissioned peer"
        )
    return value


# concurrent or incomplete quit evidence cannot identify the cause of a process exit
def quit_disposition(root, active, epoch):
    if active is None:
        return {"disposition": "outside_owner_scheduled_quit"}
    try:
        arm, exit_sha = eligible_exit(root, active)
        if arm is None:
            return {"disposition": "outside_owner_scheduled_quit"}
        if exit_sha is not None:
            ready, _ = exit_evidence(root, arm, exit_sha)
            if same_peer(ready, epoch):
                return {
                    "disposition": "scheduled_quit_observed",
                    "scheduled_quit_intent_sha256": arm,
                    "scheduled_exit_sha256": exit_sha,
                }
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        pass
    return {"disposition": "scheduled_quit_unresolved"}


# scheduling proof must refer to the same owned process and installed inputs
def same_peer(readiness, epoch):
    return all(
        readiness[key] == epoch[key]
        for key in ("peer", "installation_sha256", "lifecycle_sha256")
    )
