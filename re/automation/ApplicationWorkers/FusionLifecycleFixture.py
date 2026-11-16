import argparse
import json
import os
import sqlite3
import sys
import time
from contextlib import closing, contextmanager
from pathlib import Path

import ApplicationProtocol as protocol
import FusionLifecycleOwner as driver
from ApplicationProtocol import encoded, file_bytes, record, sha256, write_new
from FusionExitEvidence import seal_and_watch
from FusionExitFixture import ready_grant
from FusionQuitAuthorization import authorize, paths
from FusionQuitRelease import bind_replacement
from FusionReplacementLaunch import replacement_paths
from MacApplicationPeer import process_peer


class Disposable:
    def __init__(self, mode, replacement):
        self.mode = mode
        self.replacement = replacement

    def watch(
        self, installation, store, queue, lifecycle, seconds, *, request_quit, admit
    ):
        assert request_quit and queue.is_file()
        config = record(installation)
        root = Path(config["endpoint"])
        fence = file_bytes(root / "fence.json")
        handoff = json.loads(fence)
        active = record(root / driver.ACTIVE)
        old = process_peer(handoff["host"]["pid"])
        readiness = {
            **ready_grant(
                {key: value for key, value in old.items() if key != "executable"}
            ),
            "intent_sha256": active["restart_intent_sha256"],
            "installation_sha256": sha256(file_bytes(installation)),
            "lifecycle_sha256": sha256(file_bytes(lifecycle)),
        }

        def verify():
            assert file_bytes(root / "fence.json") == fence

        def marker(_):
            suffix = (
                f"-{active['restart_intent_sha256']}"
                if self.mode == "continuous"
                else ""
            )
            write_new(root / f"fixture-watch{suffix}", b"armed\n")

        @contextmanager
        def publish(arm, deadline):
            if self.mode == "lease-expired":
                with closing(sqlite3.connect(store / "ledger.sqlite3")) as db:
                    db.execute("UPDATE jobs SET lease_until=0 WHERE state='running'")
                    db.commit()
            deadline = min(deadline, time.monotonic_ns() + admit() * 1_000_000_000)
            with authorize(
                vars(protocol),
                config,
                root,
                readiness,
                old["executable"],
                arm,
                deadline,
                process_peer,
                "b" * 64,
                "a" * 64,
            ) as evidence:
                if self.mode == "quit-lost":
                    os._exit(73)
                files = paths(root, readiness["intent_sha256"])
                request = sha256(file_bytes(files["request"]))
                write_new(
                    files["attempt"],
                    encoded(
                        {"version": 1, "request_sha256": request, "status": "reserved"}
                    ),
                )
                (root / "stop-fixture").touch()
                yield evidence

        observed = seal_and_watch(
            root,
            readiness,
            old["executable"],
            sha256(fence),
            seconds,
            verify,
            marker,
            authorize=publish,
        )
        assert observed["status"] == "exact_exit_observed"
        if self.mode == "continuous":
            return observed
        os._exit(73)

    def launch(self, args, root, config, installation, *, admit):
        assert config["source_revision"] and record(args.queue_receipt)["jobs"]["b"]
        assert admit() > 0
        request, receipt = replacement_paths(root, args.quit_intent_sha256)
        active = record(root / driver.ACTIVE)
        body = {
            "version": 1,
            "scope": "owner_fusion_replacement_request",
            "quit_intent_sha256": args.quit_intent_sha256,
            "quit_exit_sha256": args.quit_exit_sha256,
            "restart_intent_sha256": active["restart_intent_sha256"],
            "installation_sha256": sha256(installation),
            "fence_sha256": sha256(file_bytes(root / "fence.json")),
            "handoff_id": active["handoff_id"],
        }
        peer = process_peer(self.replacement)
        request_bytes = encoded(body)
        write_new(request, request_bytes)
        bind_replacement(
            vars(protocol), root, body, sha256(request_bytes), peer["executable"]
        )
        if self.mode == "launch-exit":
            write_new(
                receipt,
                encoded(
                    {
                        "launch_request_sha256": sha256(request_bytes),
                        "peer": {
                            key: value
                            for key, value in peer.items()
                            if key != "executable"
                        },
                    }
                ),
            )
            (root / "fence.json").unlink()
        else:
            assert self.mode == "launch-lost"
        os._exit(73)

    def phase_b(self, args, root, config, installation):
        assert (
            self.mode == "final-lost"
        ), "Phase B verifier was called before eligibility"
        assert config["source_revision"] and installation == file_bytes(
            args.installation
        )
        _, receipt = replacement_paths(root, args.quit_intent_sha256)
        assert args.launch_receipt_sha256 == sha256(file_bytes(receipt))
        launch = record(receipt)
        peer = process_peer(self.replacement)
        assert launch["peer"] == {
            key: value for key, value in peer.items() if key != "executable"
        }
        queue = record(args.queue_receipt)
        active = record(root / driver.ACTIVE)
        current, _ = driver.phase_state(args.store, queue, active, 10, 60)
        assert current["state"] == "completed"
        write_new(root / "fixture-phase-b", b"verified\n")
        return {
            "status": "replacement_phase_b_verified",
            "phase_b_receipt_sha256": current["receipt"],
            "phase_b_result_sha256": current["result"],
            "readiness_probe_sha256": "c" * 64,
            "peer": launch["peer"],
            "native_qualified": False,
        }


def main():
    if sys.argv[1] == "acceptance-crash":
        del sys.argv[1]
        return acceptance_crash()
    if sys.argv[1] == "legacy-timeout":
        print(json.dumps(legacy_timeout(Path(sys.argv[2]))))
        return 0
    fixture = argparse.ArgumentParser()
    fixture.add_argument("mode")
    fixture.add_argument("replacement", type=int)
    opts, owner_args = fixture.parse_known_args()
    disposable = Disposable(opts.mode, opts.replacement)
    driver.watch = disposable.watch
    driver.request_launch = disposable.launch
    driver.read_launch = disposable.phase_b
    if opts.mode == "final-lost":
        seal = driver.seal

        def stop_after_final(path, raw):
            seal(path, raw)
            os._exit(73)

        driver.seal = stop_after_final
    sys.argv[1:] = owner_args
    return driver.main()


def acceptance_crash():
    from Adapters import A03Adapter
    from Supervisor import main

    finish = A03Adapter.FinishJob

    def stop_after_a(self, path, outcome, result, reason):
        response = finish(self, path, outcome, result, reason)
        if outcome == "completed" and response["stale"] is False:
            os._exit(74)
        return response

    A03Adapter.FinishJob = stop_after_a
    return main()


def legacy_timeout(store):
    from Ledger import Ledger
    from RecoveryFence import owner_digest, rotate_owner

    resource = "application:solidworks:legacy-fixture"
    kind = "fixture.timeout"
    worker = "fixture:legacy"
    revision = "d" * 40
    with Ledger(store) as ledger:
        owner = "f" * 64
        rotate_owner(ledger, owner)
        ledger.resource(resource, available=True, capacity=1)
        ledger.pool("timeout", [kind])
        ledger.submit(
            {
                "id": worker,
                "kind": kind,
                "resources": [resource],
                "inputs": {},
                "rule_version": "fixture@1",
                "tool_version": revision,
                "options": {"source_revision": revision},
            }
        )
        claim = ledger.claim(worker, "timeout")
        timeout = {
            "version": 1,
            "installation": "solidworks:legacy-fixture",
            "source_revision": revision,
            "queue_job_id": "e" * 32,
            "request_sha256": "c" * 64,
            "nonce": "b" * 48,
            "client": {"pid": 1, "started": "windows:1"},
            "job_id": worker,
            "kind": kind,
            "resources": [resource],
            "session": "fixture",
            "generation": claim["generation"],
            "fingerprint": claim["fingerprint"],
            "attempt": claim["attempt"],
        }
        result = {
            "session_version": 1,
            "receipt": {
                "receipt_version": 1,
                "job_id": worker,
                "attempt": claim["attempt"],
                "session": "fixture",
                "orphan": False,
                "stop_reason": None,
                "exit_status": 0,
                "signal": None,
            },
            "result": {
                "outcome": "waiting_application",
                "records": {
                    "installation": timeout["installation"],
                    "application": "solidworks",
                    "claim": "unqualified_dispatch",
                    "native_qualified": False,
                    "queue_timeout": timeout,
                },
            },
        }
        ledger.finish(
            worker,
            claim["lease_token"],
            "waiting_application",
            None,
            "legacy fixture timeout",
            result_record=result,
            owner_pin=owner_digest(owner),
        )
        return dict(
            ledger.db.execute(
                "SELECT resource,epoch,job_id,receipt,result FROM application_holds WHERE resource=?",
                (resource,),
            ).fetchone()
        )


if __name__ == "__main__":
    sys.exit(main())
