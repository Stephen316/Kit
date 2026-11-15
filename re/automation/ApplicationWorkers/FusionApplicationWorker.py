import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import time

from ApplicationProtocol import QueueClient, WaitingApplication, configuration, file_bytes, load_pinned, pin, record, require, sha256, write_new, write_record
from FusionRestart import wait_for_restart


def input_file(session, job, role, limit=256 * 1024 * 1024):
    require(role in job["inputs"], f"missing application input role: {role}")
    item = job["inputs"][role]
    require(isinstance(item["sha256"], str) and re.fullmatch("[0-9a-f]{64}", item["sha256"]), "invalid application input digest")
    require(item["path"] == f"inputs/{item['sha256']}", "application input is outside the private session")
    source = session / item["path"]
    raw = file_bytes(source, limit)
    require(sha256(raw) == item["sha256"], "application input digest changed")
    return source, raw


def accepted_first(session, job, config, plan_hash):
    _, raw = input_file(session, job, "phase-a.accepted", limit=1024 * 1024)
    accepted = json.loads(raw)
    result_sha256 = sha256(raw)
    dependency = job["dependencies"].get(accepted["receipt"]["job_id"])
    require(dependency is not None and dependency["result"] == result_sha256,
            "phase B requires the accepted phase A result as a completed controller dependency")
    result = accepted["result"]
    records = result["records"]
    require(accepted["output_artifacts_version"] == 1 and result["outcome"] == "completed" and records["plan_sha256"] == plan_hash
            and records["phase"] == "a" and records["installation"] == config["installation"],
            "accepted phase A provenance does not match this installation and plan")
    return accepted


def stage_plan(client, session, job, raw, plan, plan_hash, accepted):
    write_new(client.directory / "plan.json", raw)
    if accepted is not None:
        prior = client.directory / "phase-a"
        prior.mkdir(mode=0o700)
        names = {"phase-a.receipt": "receipt.json", "phase-a.measurements": "measurements.json"}
        names.update({f"phase-a.{recipe}": f"{recipe}-fusion-fresh-baseline-a.f3d" for recipe in plan["recipes"]})
        prior_bytes = 0
        for role, name in names.items():
            source, raw = input_file(session, job, role)
            expected = accepted["output_artifacts"][role]
            require(sha256(raw) == expected["sha256"] and len(raw) == expected["size_bytes"],
                    "phase A input differs from the accepted controller artifact")
            prior_bytes += len(raw)
            require(prior_bytes <= 256 * 1024 * 1024, "prior phase A inputs exceed 256 MiB")
            write_new(prior / name, raw)
        receipt = record(prior / "receipt.json")
        measurements = record(prior / "measurements.json")
        require(receipt["status"] == "complete" and receipt["phase"] == "a"
                and receipt["plan_sha256"] == plan_hash
                and receipt["measurements_sha256"] == sha256(file_bytes(prior / "measurements.json"))
                and measurements["status"] == "complete", "phase A inputs are incomplete or belong to a different plan")


def collect(session, client, response, plan_hash, phase):
    from ApplicationProtocol import identity

    require(response["proof"]["claim"] == "unqualified_application_observation"
            and response["proof"]["phase"] == phase and response["proof"]["plan_sha256"] == plan_hash,
            "application phase proof differs from this request")
    files = response["files"]
    require(isinstance(files, dict) and len(files) <= 63
            and sum(item["size_bytes"] for item in files.values()) <= 256 * 1024 * 1024, "invalid application output roster")
    for item in files.values():
        relative = item["path"]
        require(relative.startswith(f"phase-{phase}/") and len(Path(relative).parts) == 2
                and Path(relative).name not in ("", ".", "..") and "\\" not in relative,
                "application output escapes its phase directory")
    artifacts = client.copy_files(session / "work", response)
    if phase == "b":
        previous = record(client.directory / "phase-a/measurements.json")["process"]
        require(previous["pid"] != response["host"]["pid"] and identity(previous["pid"]) is None,
                "phase B requires the old Fusion process to have exited")
    write_record(session / "work/dispatch.json", response)
    artifacts["dispatch"] = pin(session / "work/dispatch.json", "dispatch.json")
    require(sum(item["size_bytes"] for item in artifacts.values()) <= 256 * 1024 * 1024,
            "application outputs and dispatch receipt exceed 256 MiB")
    return artifacts


def dispatch(session, config):
    job = record(session / "job.json")
    require(job["session_version"] == 1 and set(job["job"]["options"]) == {"phase"}, "application job takes only a phase option")
    phase = job["job"]["options"]["phase"]
    require(phase in ("a", "b"), "application job phase must be a or b")
    records = {"installation": config["installation"], "application": config["application"],
               "phase": phase, "claim": "unqualified_dispatch", "native_qualified": False}
    if config["application"] != "fusion" or sys.platform != "darwin":
        return {"outcome": "waiting_application", "reason": "this installation has no qualified Fusion fresh-phase counterpart on this platform", "records": records}
    deadline = min(job["stop_at"] - 1, time.time() + 300)
    require(deadline > time.time(), "application session has no remaining dispatch budget")
    client = None
    try:
        load_pinned(config, "re/automation/ApplicationWorkers/ApplicationProtocol.py")
        _, raw = input_file(session, job, "plan", limit=1024 * 1024)
        plan = json.loads(raw)
        require(plan["source_revision"] == config["source_revision"], "plan and installation source revisions differ")
        plan_hash = sha256(raw)
        accepted = None
        if phase == "b":
            accepted = accepted_first(session, job, config, plan_hash)
            wait_for_restart(config, accepted["result"]["records"], plan_hash, deadline)
        client = QueueClient(config, deadline)
        stage_plan(client, session, job, raw, plan, plan_hash, accepted)
        probe = client.call("probe", {"plan_sha256": plan_hash})
        require(probe["proof"]["control"] == "healthy" and probe["proof"]["host"] == probe["host"]
                and probe["proof"]["plan_sha256"] == plan_hash and probe["proof"]["documents_after"] == 0
                and 0 <= time.time() - probe["proof"]["measured_at"] <= 60, "application readiness lacks fresh pinned control evidence")
        response = client.call("phase", {"phase": phase, "plan_sha256": plan_hash,
                                         "probe_sha256": sha256(file_bytes(client.directory / "probe.done"))})
        artifacts = collect(session, client, response, plan_hash, phase)
        records.update({"plan_sha256": plan_hash, "host": response["host"], "fusion_version": response["proof"]["fusion_version"],
                        "restart_handoff": response["proof"].get("restart_handoff")})
        return {"outcome": "completed", "reason": response["reason"], "records": records, "artifacts": artifacts}
    except (WaitingApplication, FileNotFoundError, BlockingIOError) as error:
        return {"outcome": "waiting_application", "reason": str(error)[:2048], "records": records}
    finally:
        if client is not None:
            client.close()


def interrupted(number, frame):
    raise InterruptedError("application worker interrupted; external CAD remains owned by its launcher")


def main():
    parser = argparse.ArgumentParser(description="Dispatch pinned Fusion phases to a private local add-in queue")
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("session", type=Path)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    session = args.session.resolve(strict=True)
    try:
        config = configuration(args.installation)
        result = dispatch(session, config)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"outcome": "rejected", "reason": f"{type(error).__name__}: {error}"[:2048],
                  "records": {"claim": "unqualified_dispatch", "native_qualified": False}}
    write_record(session / "result.json", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
