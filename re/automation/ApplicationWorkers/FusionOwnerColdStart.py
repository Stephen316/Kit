import argparse
import json
import math
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import ApplicationProtocol as protocol
import FusionStartupEvidence as startup
from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    directory,
    encoded,
    file_bytes,
    owner_lock,
    require,
    sha256,
    write_new,
)
from FusionLifecycleRecords import optional
from FusionExitRecords import pin
from FusionLifecycleRegistration import checked_policy
from FusionQueueReceipt import owned_bytes, seal
from FusionReplacementLaunch import replacement_source
from FusionStartupProvision import StartupUnavailable, observe, owner_inputs
from MacApplicationBundle import pinned_bundle
from MacApplicationPeer import process_peer
from MacBundleLaunch import MacLaunchError, available, launch_bundle
from QueueFusionPhases import recover_receipt
from FusionColdStartAdmission import (
    admit,
    exact_record,
    initial_snapshot,
    prior,
    reserve,
)
from Ledger import Ledger
from StoreRead import read_store
from Supervisor import read_config

REQUEST = "cold-start-request.json"
ATTEMPT = "cold-start-launch.json"
PEER = "cold-start-peer.json"
EXTRA_POLICY = (
    "FusionColdStartAdmission.py",
    "ApplicationWorkers/FusionOwnerColdStart.py",
    "ApplicationWorkers/MacBundleLaunch.py",
)


class ColdStart:
    def __init__(self, args):
        self.args = args
        self.config, self.installation, self.lifecycle_sha, self.executable = (
            owner_inputs(
                args.installation,
                args.lifecycle,
            )
        )
        self.configuration = file_bytes(args.config)
        settings = read_config(args.config)
        controller = settings["controller"]
        require(
            set(controller) == {"adapter", "store"} and controller["adapter"] == "a03",
            "Fusion initial startup requires the built-in A03 controller",
        )
        self.store = directory(controller["store"])
        self.root = directory(self.config["endpoint"])
        self.queue = recover_receipt(args.config, args.queue_receipt)
        self.queue_raw = owned_bytes(args.queue_receipt)
        require(
            settings["resources"].get(self.queue["resource"]) == 1,
            "Fusion initial startup requires the configured capacity-one resource",
        )
        self.install_pin = checked_policy(
            self.config, self.queue["resource"], extra=EXTRA_POLICY
        )
        _, candidate = startup.profile_input(vars(protocol), args.profile)
        raw, _ = startup.verified_profile(
            vars(protocol),
            self.config,
            self.installation,
            args.profile,
            Path(candidate["installed_bootstrap"]),
            self.lifecycle_sha,
            self.executable,
        )
        self.profile_raw = raw
        self.source = replacement_source(self.config, require_admission=True)
        self.bundle = self.verify_inputs()

    def verify_inputs(self):
        lifecycle = file_bytes(self.args.lifecycle)
        require(
            file_bytes(self.args.config) == self.configuration
            and file_bytes(self.args.installation) == self.installation
            and sha256(lifecycle) == self.lifecycle_sha
            and file_bytes(self.args.profile) == self.profile_raw
            and owned_bytes(self.args.queue_receipt) == self.queue_raw,
            "Fusion initial startup inputs changed",
        )
        return pinned_bundle(lifecycle, sha256(self.installation))

    def binding(self):
        return {
            "version": 1,
            "scope": "owner_fusion_cold_start_request",
            "installation_sha256": sha256(self.installation),
            "profile_sha256": sha256(self.profile_raw),
            "lifecycle_sha256": self.lifecycle_sha,
            "source_revision": self.config["source_revision"],
            "store_path_sha256": sha256(os.fsencode(self.store)),
            "queue_receipt_sha256": sha256(self.queue_raw),
            "provider_sha256": sha256(self.source),
        }

    def check_endpoint(self):
        require(
            not any(
                os.path.lexists(self.root / path)
                for path in (
                    "fence.json",
                    ACKNOWLEDGEMENT,
                    "fusion-lifecycle-active.json",
                )
            )
            and not any(directory(self.root / "jobs", True).iterdir()),
            "Fusion initial startup requires a clear owned endpoint",
        )

    def snapshot(self, ledger):
        return initial_snapshot(
            ledger, self.queue, sha256(self.queue_raw), self.install_pin
        )

    def request(self):
        path = self.root / REQUEST
        raw = optional(path)
        if raw is not None:
            value = json.loads(raw)
            require(
                value
                == {
                    **self.binding(),
                    "admission": value["admission"],
                    "launch_challenge": value["launch_challenge"],
                },
                "existing Fusion initial startup belongs to different owner inputs",
            )
            return raw, value
        with (
            owner_lock(self.root / "dispatch.lock"),
            owner_lock(self.root / "host.lock"),
        ):
            self.check_endpoint()
            with Ledger(self.store) as ledger:
                admission = self.snapshot(ledger)
                value = {
                    **self.binding(),
                    "admission": admission,
                    "launch_challenge": secrets.token_hex(24),
                }
                raw = encoded(value)
                write_new(path, raw)
                reserve(ledger, admission, sha256(raw))
        return raw, value

    def launch(self, owner_raw, request):
        with (
            owner_lock(self.root / "dispatch.lock"),
            owner_lock(self.root / "host.lock"),
        ):
            self.check_endpoint()
            self.verify_inputs()
            with Ledger(self.store) as ledger:
                require(
                    self.snapshot(ledger) == request["admission"],
                    "initial Phase A changed before launch",
                )
                reserve(ledger, request["admission"], sha256(owner_raw))
            now = time.time()
            details = {
                "version": 1,
                "scope": "owner_fusion_cold_start_launch",
                "owner_request_sha256": sha256(owner_raw),
                "launch_challenge": request["launch_challenge"],
                "requested_at": now,
                "dispatch_before": now + self.args.launch_seconds,
            }
            path = self.root / ATTEMPT
            raw = encoded(details)
            write_new(path, raw)
        observed = launch_bundle(
            self.source,
            self.bundle,
            now,
            None,
            self.args.launch_seconds,
            path,
            sha256(raw),
            dispatch_before=details["dispatch_before"],
            cold_start=True,
        )
        receipt = {
            "version": 1,
            "scope": "owner_fusion_cold_start_process",
            "owner_request_sha256": sha256(owner_raw),
            "launch_sha256": sha256(raw),
            **observed,
        }
        write_new(self.root / PEER, encoded(receipt))
        return receipt

    def verify_launch(self, owner_raw, request, launched):
        raw = file_bytes(self.root / ATTEMPT)
        attempt = json.loads(raw)
        require(
            launched["version"] == attempt["version"] == 1
            and launched["scope"] == "owner_fusion_cold_start_process"
            and attempt["scope"] == "owner_fusion_cold_start_launch"
            and launched["owner_request_sha256"]
            == attempt["owner_request_sha256"]
            == sha256(owner_raw)
            and attempt["launch_challenge"] == request["launch_challenge"]
            and launched["launch_sha256"] == sha256(raw)
            and launched["host"]["pid"] == launched["peer"]["pid"]
            and attempt["requested_at"]
            <= launched["dispatched_at"]
            < attempt["dispatch_before"]
            <= attempt["requested_at"] + 300
            and launched["dispatched_at"]
            <= launched["peer"]["started_unix_microseconds"] / 1_000_000,
            "Fusion initial process receipt differs from its sealed launch",
        )

    def live_peer(self, launched):
        peer = startup.executable_peer(process_peer, launched["peer"]["pid"])
        require(
            peer == {**launched["peer"], "executable": os.fspath(self.executable)},
            "Fusion initial launch is no longer the exact live peer",
        )

    def prove_startup(self, request, launched):
        self.live_peer(launched)
        stop = time.monotonic() + self.args.startup_seconds
        args = SimpleNamespace(
            **vars(self.args), pid=launched["peer"]["pid"], wait_seconds=1
        )
        replies = []
        launch_pin = sha256(request["launch_challenge"].encode("ascii"))
        while time.monotonic() < stop:
            args.wait_seconds = min(
                startup.MAX_SECONDS, max(1, math.floor(stop - time.monotonic()))
            )
            try:
                observe(
                    args,
                    self.config,
                    self.installation,
                    self.lifecycle_sha,
                    self.executable,
                    launch_binding=launch_pin,
                    retain=replies.append,
                )
            except StartupUnavailable:
                continue
            (proof,) = replies
            require(
                json.loads(proof)["peer"]
                == {**launched["peer"], "executable": os.fspath(self.executable)},
                "Fusion startup response belongs to a different launch peer",
            )
            return proof
        raise StartupUnavailable("Fusion initial launch remains unverified")

    def complete(self, raw, request, launched, proof):
        self.verify_inputs()
        evidence = {
            "version": 1,
            "scope": "owner_fusion_cold_start_phase_a",
            "owner_request_sha256": sha256(raw),
            "launch_receipt_sha256": sha256(encoded(launched)),
            "startup_receipt": json.loads(proof),
            "startup_receipt_sha256": sha256(proof),
        }
        saved = encoded(evidence)
        checksum = sha256(saved)
        seal(self.root / f"cold-start-admission-{checksum}.json", saved)
        with owner_lock(self.root / "dispatch.lock"):
            self.check_endpoint()
            require(
                file_bytes(self.root / REQUEST) == raw
                and file_bytes(self.root / PEER) == encoded(launched),
                "Fusion initial launch custody changed before admission",
            )
            self.verify_launch(raw, request, launched)
            self.live_peer(launched)
            with Ledger(self.store) as ledger:
                try:
                    with owner_lock(self.root / "host.lock"):
                        raise ValueError("Fusion add-in released its live host lock")
                except BlockingIOError:
                    pass
                require(
                    0
                    <= time.time() - evidence["startup_receipt"]["observed_at"]
                    < startup.MAX_SECONDS,
                    "Fusion startup receipt expired before controller admission",
                )
                require(
                    self.snapshot(ledger) == request["admission"],
                    "initial Phase A changed before admission",
                )
                admit(ledger, request["admission"], sha256(raw), checksum)
        return self.report(request, checksum)

    def recorded(self, raw, request):
        with read_store(self.store / "ledger.sqlite3", None, (4,)) as database:
            row = prior(SimpleNamespace(db=database), self.queue["resource"])
            if row is None:
                return None
            require(
                exact_record(row, request["admission"], sha256(raw)),
                "A03 initial reservation differs",
            )
            checksum = row["startup_receipt"]
        if checksum is None:
            return None
        checksum = pin(checksum)
        receipt = file_bytes(self.root / f"cold-start-admission-{checksum}.json")
        observed = file_bytes(self.root / PEER)
        proof = json.loads(receipt)
        require(
            sha256(receipt) == checksum
            and proof["owner_request_sha256"] == sha256(raw)
            and proof["launch_receipt_sha256"] == sha256(observed)
            and sha256(encoded(proof["startup_receipt"]))
            == proof["startup_receipt_sha256"],
            "A03 initial admission lost its exact startup evidence",
        )
        self.verify_launch(raw, request, json.loads(observed))
        return self.report(request, checksum)

    def report(self, request, checksum):
        return {
            "status": "initial_phase_a_admission_recorded",
            "job": request["admission"]["phase_a"],
            "evidence_sha256": checksum,
        }

    def tick(self):
        raw, request = self.request()
        existing = self.recorded(raw, request)
        if existing is not None:
            return existing
        observed = optional(self.root / PEER)
        if observed is None:
            if os.path.lexists(self.root / ATTEMPT):
                return {"status": "cold_launch_unobserved"}
            try:
                launched = self.launch(raw, request)
            except MacLaunchError as error:
                return {
                    "status": "cold_launch_unobserved",
                    "preexisting_peer": error.returncode == 2,
                }
        else:
            launched = json.loads(observed)
        self.verify_launch(raw, request, launched)
        proof = self.prove_startup(request, launched)
        return self.complete(raw, request, launched, proof)


def main():
    parser = argparse.ArgumentParser(
        description="Start one opt-in owner Fusion session before Phase A"
    )
    for name in ("config", "installation", "lifecycle", "profile", "queue-receipt"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--launch-seconds", type=int, default=60)
    parser.add_argument("--startup-seconds", type=int, default=120)
    args = parser.parse_args()
    try:
        require(
            1 <= args.launch_seconds <= 300 and 1 <= args.startup_seconds <= 300,
            "invalid Fusion initial startup budget",
        )
        available()
        owner = ColdStart(args)
        with owner_lock(owner.root / "cold-start.lock"):
            report = owner.tick()
        print(encoded(report).decode(), end="")
        return 0 if report["status"] == "initial_phase_a_admission_recorded" else 2
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        OverflowError,
        RecursionError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion initial startup unavailable ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
