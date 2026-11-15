import argparse
import json
import os
from pathlib import Path
import signal
import time

import ApplicationProtocol
from ApplicationProtocol import HostQueue, QueueClient, WaitingApplication, configuration, file_bytes, load_pinned, pin, record, require, sha256, write_record
from FusionRestart import wait_for_restart


def owner_restart_output(host, value, work):
    from FusionOwnerRestart import start_seconds
    from FusionPhasePlan import phase_paths

    plan_hash = value["body"]["plan_sha256"]
    phase = work / "phase-a"
    phase.mkdir(mode=0o700)
    process = {"pid": host.host["pid"], "start_unix_seconds": start_seconds(host.host)}
    provenance = {"schema": 1, "phase": "a", "status": "complete", "plan_sha256": plan_hash}
    report = {**provenance, "source_revision": host.config["source_revision"],
              "fixture_only": True, "fusion_version": "fixture build", "errors": [],
              "process": process, "previous_measurements_sha256": None, "ended_unix_seconds": time.time()}
    measures = phase / "measurements.json"
    write_record(measures, report)
    write_record(phase / "receipt.json", {**provenance, "measurements_sha256": sha256(file_bytes(measures))})
    for recipe in ("P01", "P04"):
        (phase / f"{recipe}-fusion-fresh-baseline-a.f3d").write_bytes(b"non-CAD fixture content")
    proof = {"claim": "unqualified_application_observation", "fixture_only": True,
             "phase": "a", "plan_sha256": plan_hash, "fusion_version": "fixture build",
             "host": host.host, "restart_handoff": host.restart_handoff(value, plan_hash)}
    files = {role: pin(work / path, path) for role, path in phase_paths({"recipes": ["P01", "P04"]}, "a").items()}
    return "completed", "fixture restart transport only", proof, files


def run_host(config, use_counterpart=False, owner_restart=False):
    provider = ApplicationProtocol.FUSION_PROVIDER if owner_restart else "fixture.transport"
    host = HostQueue(config, provider=provider)
    counterpart = load_pinned(config, ApplicationProtocol.COUNTERPART) if use_counterpart else None
    if counterpart is not None:
        counterpart["protocol"] = vars(ApplicationProtocol)
    stopped = False

    def stop(number, frame):
        nonlocal stopped
        stopped = True

    def action(value, work):
        mode = value["body"]["mode"]
        if mode == "wait":
            write_record(host.root / "entered.json", {"work": str(work)})
            until = time.monotonic() + 30
            while not (host.root / "release.json").exists() and time.monotonic() < until:
                time.sleep(0.02)
        proof = {"claim": "transport_fixture", "native_qualified": False}
        if value["operation"] == "probe":
            return "completed", "fixture challenge", proof, {}
        if owner_restart:
            return owner_restart_output(host, value, work)
        relative = "nested/fixture.bin" if mode == "resume" else "fixture.bin"
        output = work / relative
        if mode == "resume":
            output.parent.mkdir(mode=0o700)
        output.write_bytes(b"real filesystem transport bytes")
        if "plan_sha256" in value["body"]:
            proof["plan_sha256"] = value["body"]["plan_sha256"]
        if mode == "handoff":
            proof["restart_handoff"] = host.restart_handoff(value, "f" * 64)
        return "completed", "fixture transport only", proof, {"fixture": pin(output, relative)}

    signal.signal(signal.SIGTERM, stop)
    write_record(host.root / "ready.json", {"host": host.host}, replace=True)
    try:
        while not stopped and not (host.root / "stop-fixture").exists():
            path = host.next_path()
            if path is None:
                time.sleep(0.02)
                continue
            if counterpart is not None:
                counterpart["serve"](host, path, None)
            else:
                host.perform(path, action)
    finally:
        host.close()


def run_client(config, mode, seconds):
    client = None
    try:
        client = QueueClient(config, time.time() + seconds, provider="fixture.transport")
        if mode == "queued":
            client.call("phase", {"mode": "echo"})
        else:
            client.call("probe", {"mode": "echo"})
            response = client.call("phase", {"mode": mode})
            if mode == "copied":
                work = Path(config["endpoint"]).parent / "Session/work"
                work.mkdir(mode=0o700, parents=True)
                artifacts = client.copy_files(work, response)
                write_record(Path(config["endpoint"]) / "copied.json", {"work": str(work), "spool": str(client.directory), "artifacts": artifacts})
                until = time.monotonic() + 30
                while not (Path(config["endpoint"]) / "release-client.json").exists() and time.monotonic() < until:
                    time.sleep(0.02)
            print(json.dumps(response), flush=True)
    except WaitingApplication as error:
        print(json.dumps({"outcome": "waiting_application", "reason": str(error), "native_qualified": False}), flush=True)
    finally:
        if client is not None:
            client.close()


def run_restart(config, input_file, seconds):
    value = record(input_file)
    write_record(Path(config["endpoint"]) / "restart-wait.json", {"entered": True}, replace=True)
    try:
        wait_for_restart(config, value["records"], value["plan_sha256"], time.time() + seconds)
        result = {"status": "ready"}
    except WaitingApplication as error:
        result = {"status": "waiting_application", "reason": str(error)}
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": "rejected", "reason": str(error)}
    print(json.dumps(result), flush=True)


def run_native_startup(config, stage):
    host = HostQueue(config)
    try:
        before = host.fenced()
        if stage != "startup-unverified":
            for role, relative in (("bootstrap", ApplicationProtocol.BOOTSTRAP),
                                   ("protocol", ApplicationProtocol.PROTOCOL)):
                raw = ApplicationProtocol.committed_bytes(config, relative)
                host.loaded_sources[role] = {
                    "path": relative, "sha256": sha256(raw), "size_bytes": len(raw),
                    "revision": config["source_revision"],
                }
        if stage == "startup-stale":
            host.loaded_sources["bootstrap"]["revision"] = "0" * 40
        print(json.dumps({"before": before, "after": host.fenced()}), flush=True)
    finally:
        host.close()


def main():
    parser = argparse.ArgumentParser(description="Real-process fixture for the local application transport; no CAD claims")
    parser.add_argument("operation", choices=("host", "client", "counterpart", "supervised", "restart", "owner-restart-host",
                                              "startup-unverified", "startup-stale", "startup-verified"))
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--mode", choices=("echo", "handoff", "wait", "queued", "copied"), default="echo")
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--session", type=Path)
    args = parser.parse_args()
    config = configuration(args.installation)
    if args.operation in ("host", "counterpart", "owner-restart-host"):
        run_host(config, args.operation == "counterpart", args.operation == "owner-restart-host")
    elif args.operation == "supervised":
        run_supervised(config, args.session)
    elif args.operation == "restart":
        run_restart(config, args.session, args.seconds)
    elif args.operation.startswith("startup-"):
        run_native_startup(config, args.operation)
    else:
        run_client(config, args.mode, args.seconds)


def supervised_restart(config, session, job, deadline):
    source = job["inputs"]["prior"]
    raw = file_bytes(session / source["path"])
    accepted = json.loads(raw)
    digest = sha256(raw)
    previous = job["dependencies"][accepted["receipt"]["job_id"]]
    require(digest == source["sha256"] == previous["result"]
            and accepted["result"]["outcome"] == "completed",
            "fixture restart requires the exact completed controller dependency")
    write_record(Path(config["endpoint"]) / "restart-wait.json", {"prior_result_sha256": digest})
    wait_for_restart(config, accepted["result"]["records"], "f" * 64, deadline)


def run_supervised(config, session):
    job = record(session / "job.json")
    options = job["job"]["options"]
    phase = options.get("phase")
    mode = options.get("mode", "owner_restart")
    if phase == "b":
        write_record(session / "result.json", {"outcome": "waiting_application", "reason": "fixture never runs phase B",
                     "records": {"claim": "unqualified_dispatch", "native_qualified": False}})
        return
    deadline = min(time.time() + (40 if mode == "after_restart" else 20), job["stop_at"] - 1)
    if mode == "after_restart":
        supervised_restart(config, session, job, deadline)
    provider = ApplicationProtocol.FUSION_PROVIDER if phase == "a" else "fixture.transport"
    plan_hash = job["inputs"]["plan"]["sha256"] if phase == "a" else "f" * 64
    client = QueueClient(config, deadline, provider=provider)
    try:
        client.call("probe", {"mode": "echo"})
        response = client.call("phase", {"mode": mode, "plan_sha256": plan_hash})
        work = session / "work"
        artifacts = client.copy_files(work, response)
        dispatch = work / "dispatch.json"
        write_record(dispatch, response)
        artifacts["dispatch"] = pin(dispatch, "dispatch.json")
        records = {"claim": "unqualified_dispatch", "native_qualified": False}
        if mode in ("handoff", "after_restart", "owner_restart"):
            records.update({"host": response["host"], "restart_handoff": response["proof"].get("restart_handoff")})
        write_record(session / "result.json", {"outcome": "completed", "reason": "transport fixture",
                     "records": records, "artifacts": artifacts})
    finally:
        client.close()


if __name__ == "__main__":
    main()
