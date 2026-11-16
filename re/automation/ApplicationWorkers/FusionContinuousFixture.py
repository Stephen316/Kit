import json
import os
import subprocess
import sys
import time
from pathlib import Path

import ApplicationProtocol as protocol
import FusionLifecycleOwner as driver
from ApplicationProtocol import (
    HostQueue,
    QueueClient,
    committed_bytes,
    configuration,
    encoded,
    file_bytes,
    pin,
    record,
    require,
    sha256,
    write_new,
    write_record,
)
from FusionExitFixture import wait_marker
from FusionLifecycleFixture import Disposable
from FusionQuitRelease import bind_replacement, permits_replacement
from FusionReplacementLaunch import replacement_paths
from FusionRestart import wait_for_restart
from MacApplicationPeer import process_peer
from ProtocolFixture import owner_restart_output


def host(installation):
    queue = HostQueue(configuration(installation))
    queue.installation_sha256 = sha256(file_bytes(installation))
    queue.mac_quit_replacement = lambda fence: permits_replacement(
        vars(protocol),
        queue,
        fence,
        process_peer,
    )
    for role, path in (
        ("bootstrap", protocol.BOOTSTRAP),
        ("protocol", protocol.PROTOCOL),
    ):
        source = committed_bytes(queue.config, path)
        queue.loaded_sources[role] = protocol.source_pin(queue.config, path, source)
    root = queue.root
    write_record(root / "ready.json", {"host": queue.host}, replace=True)
    try:
        while not (root / "stop-fixture").exists():
            if not queue.fenced():
                pending = queue.next_path()
                if pending is not None:
                    queue.perform(
                        pending, lambda request, work: output(queue, request, work)
                    )
            time.sleep(0.02)
    finally:
        queue.close()
        write_record(root / "host-stopped.json", {"host": queue.host}, replace=True)


def output(queue, request, work):
    proof = {
        "phase": request["body"]["phase"],
        "plan_sha256": request["body"]["plan_sha256"],
    }
    if request["operation"] == "probe":
        return "completed", "fixture control", proof, {}
    if proof["phase"] == "a":
        return owner_restart_output(queue, request, work)
    artifact = work / "fixture-b.bin"
    artifact.write_bytes(b"disposable phase B")
    return (
        "completed",
        "fixture readback",
        proof,
        {"fixture-b": pin(artifact, artifact.name)},
    )


def worker(installation, session):
    config = configuration(installation)
    job = record(session / "job.json")
    phase = job["job"]["options"]["phase"]
    plan = job["inputs"]["plan"]["sha256"]
    deadline = min(time.time() + 45, job["stop_at"] - 1)
    if phase == "b":
        source = job["inputs"]["phase-a.accepted"]
        raw = file_bytes(session / source["path"])
        accepted = json.loads(raw)
        upstream = accepted["receipt"]["job_id"]
        require(
            sha256(raw) == source["sha256"] == job["dependencies"][upstream]["result"],
            "disposable Phase B lost its accepted dependency",
        )
        wait_for_restart(config, accepted["result"]["records"], plan, deadline)
    client = QueueClient(config, deadline)
    try:
        client.call("probe", {"phase": phase, "plan_sha256": plan})
        response = client.call("phase", {"phase": phase, "plan_sha256": plan})
        work = session / "work"
        artifacts = client.copy_files(work, response)
        dispatch = work / "dispatch.json"
        write_record(dispatch, response)
        artifacts["dispatch"] = pin(dispatch, "dispatch.json")
        records = {
            "claim": "unqualified_dispatch",
            "native_qualified": False,
            "host": response["host"],
            "restart_handoff": response["proof"].get("restart_handoff"),
        }
        write_record(
            session / "result.json",
            {
                "outcome": "completed",
                "reason": "disposable pair",
                "records": records,
                "artifacts": artifacts,
            },
        )
    finally:
        client.close()


class Continuous(Disposable):
    # each disposable replacement remains owned until its observed exit is reaped
    def __init__(self):
        super().__init__("continuous", 0)
        self.replacement_process = None

    # normal restart checks require the observed child to disappear from the process table
    def watch(
        self, installation, store, queue, lifecycle, seconds, *, request_quit, admit
    ):
        deadline = time.monotonic() + seconds
        observed = super().watch(
            installation,
            store,
            queue,
            lifecycle,
            seconds,
            request_quit=request_quit,
            admit=admit,
        )
        process = self.replacement_process
        if process is not None:
            assert process.pid == observed["peer"]["pid"]
            assert process.wait(timeout=max(0, deadline - time.monotonic())) == 0
            self.replacement_process = None
        return observed

    def launch(self, args, root, config, installation, *, admit):
        assert admit() > 0 and config["installation"]
        active = record(root / driver.ACTIVE)
        request_path, receipt_path = replacement_paths(root, args.quit_intent_sha256)
        (root / "ready.json").unlink(missing_ok=True)
        (root / "host-stopped.json").unlink(missing_ok=True)
        (root / "stop-fixture").unlink()
        now = time.time()
        request = {
            "version": 1,
            "scope": "owner_fusion_replacement_request",
            "quit_intent_sha256": args.quit_intent_sha256,
            "quit_exit_sha256": args.quit_exit_sha256,
            "restart_intent_sha256": active["restart_intent_sha256"],
            "handoff_id": active["handoff_id"],
            "installation_sha256": sha256(installation),
            "fence_sha256": sha256(file_bytes(root / "fence.json")),
            "requested_at": now,
        }
        raw = encoded(request)
        write_new(request_path, raw)
        with (root.parent / "host.log").open("a", encoding="utf-8") as output:
            process = subprocess.Popen(
                [sys.executable, "-B", __file__, "host", str(args.installation)],
                stdout=output,
                stderr=subprocess.STDOUT,
            )
        self.replacement_process = process
        ready = wait_marker(
            root, "ready.json", process, "replacement fixture did not start"
        )["host"]
        peer = process_peer(process.pid)
        assert ready["pid"] == peer["pid"]
        bind_replacement(vars(protocol), root, request, sha256(raw), peer["executable"])
        reply = {
            "version": 1,
            "scope": "owner_fusion_replacement_observation",
            "status": "replacement_process_observed",
            "quit_intent_sha256": args.quit_intent_sha256,
            "quit_exit_sha256": args.quit_exit_sha256,
            "launch_request_sha256": sha256(raw),
            "host": ready,
            "peer": {key: value for key, value in peer.items() if key != "executable"},
            "dispatched_at": now,
        }
        write_new(receipt_path, encoded(reply))
        return reply

    def phase_b(self, args, root, config, installation):
        from Artifacts import Artifacts

        queue = record(args.queue_receipt)
        active = record(root / driver.ACTIVE)
        current, _ = driver.phase_state(args.store, queue, active, 10, 60)
        assert current["state"] == "completed"
        _, receipt = replacement_paths(root, args.quit_intent_sha256)
        raw = file_bytes(receipt)
        assert sha256(raw) == args.launch_receipt_sha256
        observed = json.loads(raw)
        accepted = record(Artifacts(args.store, create=False).path(current["result"]))
        assert accepted["result"]["records"]["host"] == observed["host"]
        assert observed["peer"]["pid"] == observed["host"]["pid"]
        assert config["source_revision"] and installation == file_bytes(
            args.installation
        )
        return {
            "status": "replacement_phase_b_verified",
            "phase_b_receipt_sha256": current["receipt"],
            "phase_b_result_sha256": current["result"],
            "readiness_probe_sha256": "c" * 64,
            "peer": observed["peer"],
            "native_qualified": False,
        }


def owner(arguments):
    providers = Continuous()
    driver.watch = providers.watch
    driver.request_launch = providers.launch
    driver.read_launch = providers.phase_b
    sys.argv[1:] = arguments
    return driver.main()


def wait_permission(root, name):
    expires = time.monotonic() + 18
    while not (root / name).is_file() and time.monotonic() < expires:
        time.sleep(0.02)
    assert (root / name).is_file(), "fixture acknowledgement barrier did not clear"


def supervisor(arguments):
    import Supervisor as supervisor_module

    root, selected = Path(arguments[0]), arguments[1]
    acknowledge = supervisor_module.acknowledge_application
    seen = 0

    def lose_reply(installation, adapter, intent, recovered):
        nonlocal seen
        if intent["job"] != selected:
            return acknowledge(installation, adapter, intent, recovered)
        seen += 1
        if seen == 1:
            write_new(root / "ack-first-lost", b"B accepted with retained spool\n")
            raise subprocess.TimeoutExpired("fixture acknowledgement", 1)
        if seen == 2:
            wait_permission(root, "ack-allow-cleanup")
            response = acknowledge(installation, adapter, intent, recovered)
            assert response == {"status": "acknowledged", "restart_retained": False}
            write_new(root / "ack-cleaned-lost", b"B cleaned before reply loss\n")
            raise subprocess.TimeoutExpired("fixture acknowledgement", 1)
        assert seen == 3 and recovered
        wait_permission(root, "ack-allow-replay")
        response = acknowledge(installation, adapter, intent, recovered)
        assert response == {"status": "no_pending_acceptance"}
        write_new(
            root / "ack-replayed", b"exact accepted B recovered without cleanup\n"
        )
        return response

    supervisor_module.acknowledge_application = lose_reply
    sys.argv[1:] = arguments[2:]
    return supervisor_module.main()


if __name__ == "__main__":
    mode, *arguments = sys.argv[1:]
    if mode == "host":
        host(Path(arguments[0]))
    elif mode == "worker":
        worker(*map(Path, arguments))
    elif mode == "owner":
        sys.exit(owner(arguments))
    else:
        sys.exit(supervisor(arguments))
