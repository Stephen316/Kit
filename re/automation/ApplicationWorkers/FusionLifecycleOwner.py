import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    directory,
    encoded,
    file_bytes,
    macos_automatic_quit,
    owner_lock,
    require,
    sha256,
    sync_directory,
    validate_configuration,
    write_new,
)
from AuditFusionPhases import validate_queue
from FusionCommissionedExit import CommissionedExit
from FusionExitRecords import pin, read_pinned
from FusionLifecyclePair import ACTIONABLE, phase_state, select_pair
from FusionLifecycleRecords import active_intent, eligible_exit, optional, pin_handoff
from FusionLifecycleRegistration import admit, pending_admission, release
from FusionOwnerRestart import record_restart
from FusionOwnerRecovery import archive_timeout
from FusionQueueReceipt import owned_bytes, receipt_bytes, seal
from FusionQuitObserver import watch
from FusionReplacementLaunch import (
    read_launch,
    replacement_paths,
    replacement_source,
    request_launch,
)
from FusionStartupProvision import StartupUnavailable
from MacBundleLaunch import available as replacement_available
from QueueFusionPhases import recover_receipt
from Supervisor import read_config

ACTIVE = "fusion-lifecycle-active.json"
RECONCILE_ERRORS = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    OverflowError,
    RecursionError,
    sqlite3.Error,
    subprocess.SubprocessError,
)


def status(state, **evidence):
    return {"status": state, **evidence}


class Owner:
    def __init__(self, args):
        self.args = args
        self.exit_watch = None
        self.installation_bytes = file_bytes(args.installation)
        self.config = validate_configuration(json.loads(self.installation_bytes))
        require(
            macos_automatic_quit(self.config),
            "owner lifecycle requires the macOS Fusion opt-in",
        )
        replacement_available()
        replacement_source(self.config, require_admission=True)
        self.root = directory(self.config["endpoint"])
        self.inbox = directory(args.queue_directory)
        self.lifecycle_sha = sha256(
            file_bytes(directory(args.lifecycle.parent) / args.lifecycle.name)
        )
        self.supervisor_bytes = file_bytes(args.config)
        supervisor = read_config(args.config)
        self.supervisor_state = supervisor["state"]
        controller = supervisor["controller"]
        require(
            controller.get("adapter") == "a03"
            and set(controller) == {"adapter", "store"},
            "Fusion lifecycle requires the configured A03 store",
        )
        self.store = directory(controller["store"])
        self.grace = supervisor["grace"]

    def check_configuration(self):
        require(
            file_bytes(self.args.installation) == self.installation_bytes
            and file_bytes(self.args.config) == self.supervisor_bytes
            and sha256(file_bytes(self.args.lifecycle)) == self.lifecycle_sha,
            "Fusion owner lifecycle configuration changed",
        )

    def begin(self):
        raw = optional(self.root / "fence.json")
        fence = json.loads(raw) if raw is not None else None
        recovered = archive_timeout(self, fence)
        if recovered is not None:
            return recovered
        if fence is None:
            return status("waiting_for_acknowledged_phase_a")
        if (
            fence.get("reason") != "restart_required"
            or fence.get("installation") != self.config["installation"]
        ):
            return status("waiting_for_acknowledged_phase_a")
        if os.path.lexists(self.root / ACKNOWLEDGEMENT) or any(
            directory(self.root / "jobs").iterdir()
        ):
            return status("waiting_for_acknowledged_phase_a")
        selected = select_pair(self.store, self.inbox, self.config, fence)
        if selected is None:
            return status("waiting_for_exact_queue_receipt")
        queue_path, queue, state = selected
        if state not in ACTIONABLE:
            return status("phase_b_ineligible", controller_state=state)
        require(
            recover_receipt(self.args.config, queue_path) == queue,
            "Fusion queue receipt changed during intake",
        )
        queue_raw = owned_bytes(queue_path)
        verified = record_restart(self.args.installation, self.store, queue_path)
        restart_sha = pin(verified["intent_sha256"])
        intent_path = self.root / f"restart-intent-{pin_handoff(fence['job_id'])}.json"
        intent = read_pinned(intent_path, restart_sha)
        require(
            intent["restart_handoff"] == fence
            and intent["queue_receipt_sha256"] == sha256(queue_raw)
            and intent["installation_sha256"] == sha256(self.installation_bytes)
            and intent["store_path_sha256"] == sha256(os.fsencode(self.store)),
            "Fusion restart differs from the selected receipt or fence",
        )
        active = active_intent(
            queue_path, queue_raw, restart_sha, intent, self.lifecycle_sha
        )
        write_new(self.root / ACTIVE, encoded(active))
        return self.advance(active, queue_path, queue)

    def resume(self, raw):
        active = json.loads(raw)
        name = active["queue"]
        require(
            isinstance(name, str)
            and Path(name).name == name
            and name.endswith(".json"),
            "invalid queued receipt path in Fusion lifecycle",
        )
        path = self.inbox / name
        try:
            queue_raw = owned_bytes(path)
        except FileNotFoundError:
            recover_receipt(self.args.config, path)
            queue_raw = owned_bytes(path)
        restart_sha = pin(active["restart_intent_sha256"])
        intent_path = (
            self.root / f"restart-intent-{pin_handoff(active['handoff_id'])}.json"
        )
        intent = read_pinned(intent_path, restart_sha)
        require(
            active
            == active_intent(path, queue_raw, restart_sha, intent, self.lifecycle_sha)
            and intent["queue_receipt_sha256"] == sha256(queue_raw)
            and intent["installation_sha256"] == sha256(self.installation_bytes)
            and intent["store_path_sha256"] == sha256(os.fsencode(self.store)),
            "active Fusion lifecycle differs from the accepted owner inputs",
        )
        return self.advance(active, path, validate_queue(json.loads(queue_raw)))

    def advance(self, active, queue_path, queue):
        if self.exit_watch is not None:
            self.exit_watch.planned = active
        final_path = (
            self.root / f"fusion-lifecycle-{active['restart_intent_sha256']}.json"
        )
        if pending_admission(self.store, queue, self.config, active, final_path):
            with owner_lock(self.root / "dispatch.lock"):
                verified = record_restart(
                    self.args.installation, self.store, queue_path, check=True
                )
                require(
                    verified["intent_sha256"] == active["restart_intent_sha256"],
                    "drained Fusion acknowledgement belongs to another intent",
                )
                admit(self.store, queue, self.config, active)
        current, budget = phase_state(
            self.store, queue, active, self.grace, self.args.wait_seconds
        )
        final = optional(final_path)
        if final is not None:
            return self.finish(queue, active, json.loads(final))
        arm, exit_sha = eligible_exit(self.root, active)
        if arm is None:
            if not budget:
                return pending_phase(current)
            watch(
                self.args.installation,
                self.store,
                queue_path,
                self.args.lifecycle,
                budget,
                request_quit=True,
                admit=self.admission(queue, active, current),
            )
            arm, exit_sha = eligible_exit(self.root, active)
        if exit_sha is None:
            return status("quit_exit_unobserved", request_sealed=arm is not None)
        return self.replacement(active, queue_path, queue, final_path, arm, exit_sha)

    def replacement(self, active, queue_path, queue, final_path, arm, exit_sha):
        current, budget = phase_state(
            self.store, queue, active, self.grace, self.args.wait_seconds
        )
        request_path, observation_path = replacement_paths(self.root, arm)
        launch = optional(observation_path)
        args = SimpleNamespace(
            installation=self.args.installation,
            store=self.store,
            queue_receipt=queue_path,
            lifecycle=self.args.lifecycle,
            quit_intent_sha256=arm,
            quit_exit_sha256=exit_sha,
        )
        if launch is None:
            if os.path.lexists(request_path):
                return status("replacement_unobserved", request_sealed=True)
            if not budget:
                return pending_phase(current)
            args.wait_seconds = budget
            request_launch(
                args,
                self.root,
                self.config,
                self.installation_bytes,
                admit=self.admission(queue, active, current),
            )
            launch = file_bytes(observation_path)
            current, budget = phase_state(
                self.store, queue, active, self.grace, self.args.wait_seconds
            )
        if current["state"] != "completed":
            return pending_phase(current, budget)
        args.launch_receipt_sha256 = sha256(launch)
        verified = read_launch(args, self.root, self.config, self.installation_bytes)
        if verified["status"] != "replacement_phase_b_verified":
            return status(
                "waiting_for_phase_b", controller_state=verified["controller_state"]
            )
        result = {
            "version": 1,
            "scope": "fusion_owner_lifecycle",
            "active_sha256": sha256(encoded(active)),
            "restart_intent_sha256": active["restart_intent_sha256"],
            "quit_intent_sha256": arm,
            "quit_exit_sha256": exit_sha,
            "launch_receipt_sha256": args.launch_receipt_sha256,
            "phase_b": verified,
        }
        seal(final_path, receipt_bytes(result))
        return self.finish(queue, active, result)

    def admission(self, queue, active, initial):
        def check():
            self.check_configuration()
            replacement_available()
            current, budget = phase_state(
                self.store, queue, active, self.grace, self.args.wait_seconds
            )
            require(
                budget > 0
                and all(
                    current[key] == initial[key]
                    for key in ("id", "attempts", "fingerprint", "generation")
                ),
                "the exact Fusion Phase B claim no longer admits a new physical request",
            )
            return budget

        return check

    def finish(self, queue, active, final):
        arm, exit_sha = eligible_exit(self.root, active)
        require(
            arm is not None and exit_sha is not None,
            "Fusion final evidence lost its exit",
        )
        _, launch_path = replacement_paths(self.root, arm)
        launch = read_pinned(launch_path, final["launch_receipt_sha256"])
        current, _ = phase_state(
            self.store,
            queue,
            active,
            self.grace,
            self.args.wait_seconds,
            verify_complete=True,
        )
        require(
            final["version"] == 1
            and final["scope"] == "fusion_owner_lifecycle"
            and final["active_sha256"] == sha256(encoded(active))
            and final["restart_intent_sha256"] == active["restart_intent_sha256"]
            and final["quit_intent_sha256"] == arm
            and final["quit_exit_sha256"] == exit_sha
            and current["state"] == "completed"
            and final["phase_b"]["status"] == "replacement_phase_b_verified"
            and final["phase_b"]["native_qualified"] is False
            and final["phase_b"]["peer"] == launch["peer"]
            and pin(final["phase_b"]["readiness_probe_sha256"])
            and final["phase_b"]["phase_b_receipt_sha256"] == current["receipt"]
            and final["phase_b"]["phase_b_result_sha256"] == current["result"],
            "durable Fusion lifecycle result differs from its accepted receipts",
        )
        marker = self.root / ACTIVE
        require(
            file_bytes(marker) == encoded(active), "active Fusion lifecycle changed"
        )
        final_path = (
            self.root / f"fusion-lifecycle-{active['restart_intent_sha256']}.json"
        )
        try:
            released = release(
                self.store,
                queue,
                self.config,
                active,
                final_path,
                receipt_bytes(final),
                supervisor_state=self.supervisor_state,
                final=final,
            )
        except BlockingIOError:
            released = False
        if not released:
            return status("waiting_for_phase_b_acknowledgement")
        marker.unlink()
        sync_directory(marker.parent)
        return status("lifecycle_verified", **final)

    def tick(self):
        self.check_configuration()
        raw = optional(self.root / ACTIVE)
        return self.resume(raw) if raw is not None else self.begin()


def pending_phase(current, budget=0):
    phase = current["state"]
    if phase == "queued":
        return status("waiting_for_phase_b_claim", controller_state=phase)
    return status(
        "waiting_for_phase_b" if budget else "phase_b_ineligible",
        controller_state=phase,
    )


def initial_startup(owner, args):
    if args.profile is None and args.queue_receipt is None:
        return None
    require(
        args.profile is not None and args.queue_receipt is not None,
        "initial Fusion startup requires both the profile and queue receipt",
    )
    require(
        args.queue_receipt.suffix == ".json"
        and directory(args.queue_receipt.parent) == owner.inbox,
        "initial Fusion queue receipt must be visible to the lifecycle owner",
    )
    require(
        1 <= args.launch_seconds <= 300 and 1 <= args.startup_seconds <= 300,
        "invalid Fusion initial startup budget",
    )
    from FusionOwnerColdStart import ColdStart

    boot = ColdStart(
        SimpleNamespace(
            config=args.config,
            installation=args.installation,
            lifecycle=args.lifecycle,
            profile=args.profile,
            queue_receipt=args.queue_receipt,
            launch_seconds=args.launch_seconds,
            startup_seconds=args.startup_seconds,
        )
    )
    require(
        boot.root == owner.root
        and boot.store == owner.store
        and boot.installation == owner.installation_bytes
        and boot.configuration == owner.supervisor_bytes
        and boot.lifecycle_sha == owner.lifecycle_sha,
        "initial Fusion startup differs from the pinned owner lifecycle",
    )
    return boot


def main():
    parser = argparse.ArgumentParser(
        description="Advance the exact owned Fusion lifecycle"
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--lifecycle", required=True, type=Path)
    parser.add_argument("--queue-directory", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--queue-receipt", type=Path)
    parser.add_argument("--launch-seconds", type=int, default=60)
    parser.add_argument("--startup-seconds", type=int, default=120)
    parser.add_argument("--launch-archived-replacement", action="store_true")
    parser.add_argument("--measure-archived-replacement", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=60)
    parser.add_argument("--poll-seconds", type=int, default=2)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--reset-evidence-pid", type=int)
    parser.add_argument("--reset-evidence-limit", type=int, default=50)
    args = parser.parse_args()
    if args.reset_evidence_pid is None and args.queue_directory is None:
        parser.error("--queue-directory is required for the Fusion lifecycle loop")
    if args.reset_evidence_pid is not None and (
        args.profile is not None
        or args.queue_receipt is not None
        or args.launch_archived_replacement
        or args.measure_archived_replacement
    ):
        parser.error("reset evidence observation cannot request initial startup")
    if args.launch_archived_replacement and (
        args.once or args.profile is None or args.queue_receipt is None
    ):
        parser.error("archive replacement requires ongoing commissioned owner custody")
    if args.measure_archived_replacement and not args.launch_archived_replacement:
        parser.error("archive control requires the authorized archive replacement route")
    try:
        if args.reset_evidence_pid is not None:
            from FusionResetEvidence import observe

            print(encoded(observe(args)).decode(), end="")
            return 0
        require(
            1 <= args.wait_seconds <= 300 and 1 <= args.poll_seconds <= 60,
            "invalid owner lifecycle time budget",
        )
        owner = Owner(args)
        with (
            owner_lock(owner.root / "fusion-lifecycle-owner.lock"),
            CommissionedExit(owner.root) as exit_watch,
        ):
            owner.exit_watch = exit_watch
            boot = initial_startup(owner, args)
            previous = None
            while True:
                starting = boot is not None
                commissioned = None
                try:
                    if boot is None:
                        result = owner.tick()
                    else:
                        owner.check_configuration()
                        with owner_lock(owner.root / "cold-start.lock"):
                            result = boot.tick()
                        if result["status"] == "initial_phase_a_admission_recorded":
                            commissioned = boot
                            boot = None
                except StartupUnavailable:
                    result = status("waiting_for_initial_startup_proof")
                except RECONCILE_ERRORS as error:
                    result = status("lifecycle_refused", error=type(error).__name__)
                if result != previous:
                    print(encoded(result).decode(), end="", flush=True)
                    previous = result
                if args.once:
                    if result["status"] == "lifecycle_refused":
                        return 1
                    return 2 if boot is not None else 0
                report_native_exit(exit_watch, commissioned, result)
                if starting and boot is None:
                    continue
                time.sleep(args.poll_seconds)
    except RECONCILE_ERRORS as error:
        print(f"Fusion lifecycle unavailable ({type(error).__name__})", file=sys.stderr)
        return 1


# optional kernel evidence must never stop normal owner reconciliation
def report_native_exit(watch, commissioned, result):
    try:
        evidence = (
            watch.arm(commissioned, result)
            if commissioned is not None
            else watch.collect()
        )
    except RECONCILE_ERRORS as error:
        evidence = status(
            "commissioned_native_exit_unobserved", error=type(error).__name__
        )
    if evidence is not None:
        print(encoded(evidence).decode(), end="", flush=True)


if __name__ == "__main__":
    sys.exit(main())
