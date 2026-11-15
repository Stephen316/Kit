import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import time

from ApplicationProtocol import (
    ApplicationTimeout, QueueClient, WaitingApplication, configuration,
    file_bytes, load_pinned, pin, record, request_link, require, require_win_sources,
    sha256, windows_phase_a, windows_process, write_new, write_record,
)
from FusionPhasePlan import check_scope_archives, check_scope_report, phase_options, phase_paths, plan_scope
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


def accepted_first(session, job, config, plan_hash, scope):
    _, raw = input_file(session, job, "phase-a.accepted", limit=1024 * 1024)
    accepted = json.loads(raw)
    result_sha256 = sha256(raw)
    dependency = job["dependencies"].get(accepted["receipt"]["job_id"])
    require(dependency is not None and dependency["result"] == result_sha256,
            "phase B requires the accepted phase A result as a completed controller dependency")
    result = accepted["result"]
    records = result["records"]
    require(accepted["output_artifacts_version"] == 1 and result["outcome"] == "completed" and records["plan_sha256"] == plan_hash
            and records["phase"] == "a" and records["installation"] == config["installation"]
            and records.get("scope") == scope,
            "accepted phase A provenance does not match this installation and plan")
    return accepted, raw


def stage_plan(client, session, job, raw, plan, plan_hash, accepted):
    write_new(client.directory / "plan.json", raw)
    if accepted is not None:
        result, result_bytes = accepted
        scope = plan_scope(plan)
        prior = client.directory / "phase-a"
        prior.mkdir(mode=0o700)
        names = phase_paths(plan, "a")
        if scope is not None:
            require(set(result["output_artifacts"]) == set(names) | {"dispatch"},
                    "accepted scope phase A output roles changed")
            write_new(prior / "accepted.json", result_bytes)
        prior_bytes = len(result_bytes) if scope is not None else 0
        for role, name in names.items():
            _, data = input_file(session, job, role)
            expected = result["output_artifacts"][role]
            require(sha256(data) == expected["sha256"] and len(data) == expected["size_bytes"],
                    "phase A input differs from the accepted controller artifact")
            prior_bytes += len(data)
            require(prior_bytes <= 256 * 1024 * 1024, "prior phase A inputs exceed 256 MiB")
            write_new(client.directory / name, data)
        receipt = record(prior / "receipt.json")
        if scope is None:
            data = file_bytes(prior / "measurements.json")
            require(receipt["status"] == "complete" and receipt["phase"] == "a"
                    and receipt["plan_sha256"] == plan_hash
                    and receipt["measurements_sha256"] == sha256(data)
                    and json.loads(data)["status"] == "complete", "phase A inputs are incomplete or belong to a different plan")
        else:
            data = file_bytes(prior / "report.json")
            report = json.loads(data)
            check_scope_report(receipt, report, data, plan_hash, "a")
            check_scope_archives(report, result["output_artifacts"], "a")


# windows evidence must bind the exact admitted process and successful native controls
def check_windows_phase(client, response, plan, plan_hash, directory, artifacts):
    proof = response["proof"]
    raw = file_bytes(directory / "measurements.json")
    report = json.loads(raw)
    sealed = record(directory / "receipt.json")
    require(sealed == {"schema": 1, "phase": "a", "status": "complete", "plan_sha256": plan_hash,
                       "measurements_sha256": sha256(raw)}
            and report["schema"] == 1 and report["phase"] == "a" and report["status"] == "complete"
            and report["plan_sha256"] == plan_hash and report["pins"] == plan["pins"]
            and report["source_revision"] == client.config["source_revision"]
            and proof["host"] == response["host"] and report["process"] == windows_process(response["host"])
            and report["fusion_version"] == proof["fusion_version"] and report["errors"] == []
            and set(report["captures"]) == set(plan["recipes"]),
            "Windows Fusion phase report does not match its receipt, plan and admitted process")
    require(all(report[label]["compute_all_return"] is True
                and report[label]["native_input"] == plan["pins"]["control"]
                for label in ("healthy_control_before", "healthy_control_after")),
            "Windows Fusion phase is missing its pinned controls")
    handoff = proof["restart_handoff"]
    require(handoff == {"installation": client.config["installation"], "job_id": client.job_id,
                        "reason": "restart_required", "host": response["host"], "plan_sha256": plan_hash,
                        "at": handoff["at"], "owner": "external_application_owner"}
            and report["ended_unix_seconds"] <= handoff["at"] <= response["finished_at"],
            "Windows Fusion restart fence does not match the admitted Phase A")
    for recipe, capture in report["captures"].items():
        saved = artifacts[f"phase-a.{recipe}"]
        require(capture["save_a"] == {"file": Path(saved["path"]).name, "sha256": saved["sha256"],
                                      "size_bytes": saved["size_bytes"]},
                "Windows Fusion native archive differs from its sealed report")


def collect(session, client, response, plan, plan_hash, phase):
    from ApplicationProtocol import identity

    scope = plan_scope(plan)
    require(response["proof"]["claim"] == "unqualified_application_observation"
            and response["proof"].get("scope") == scope
            and response["proof"]["phase"] == phase and response["proof"]["plan_sha256"] == plan_hash,
            "application phase proof differs from this request")
    files = response["files"]
    windows = windows_phase_a(client.config)
    require(isinstance(files, dict) and len(files) <= 63
            and sum(item["size_bytes"] for item in files.values()) <= 256 * 1024 * 1024, "invalid application output roster")
    report = None
    if scope is not None or windows:
        label = "Windows Fusion" if windows else "Fusion scope"
        require({role: item["path"] for role, item in files.items()} == phase_paths(plan, phase),
                f"{label} response did not contain its exact output roster")
    for item in files.values():
        relative = item["path"]
        require(relative.startswith(f"phase-{phase}/") and len(Path(relative).parts) == 2
                and Path(relative).name not in ("", ".", "..") and "\\" not in relative,
                "application output escapes its phase directory")
    artifacts = client.copy_files(session / "work", response)
    if windows:
        require_win_sources(client.config, response["proof"]["loaded_sources"])
        check_windows_phase(client, response, plan, plan_hash, session / "work/phase-a", artifacts)
    report_name = "measurements.json" if scope is None else "report.json"
    if scope is not None:
        directory = session / "work" / f"phase-{phase}"
        data = file_bytes(directory / report_name)
        report = json.loads(data)
        check_scope_report(record(directory / "receipt.json"), report, data, plan_hash, phase)
        check_scope_archives(report, artifacts, phase)
        require(report["source_revision"] == client.config["source_revision"]
                and report["process"]["pid"] == response["host"]["pid"]
                and report["application_build"] == response["proof"]["fusion_version"],
                "Fusion scope report belongs to a different installed process")
    if phase == "b":
        prior_raw = file_bytes(client.directory / "phase-a" / report_name)
        previous = json.loads(prior_raw)["process"]
        require(previous["pid"] != response["host"]["pid"] and identity(previous["pid"]) is None,
                "phase B requires the old Fusion process to have exited")
        if report is not None:
            require(report["previous_phase_report_sha256"] == sha256(prior_raw)
                    and report["previous_process"] == previous,
                    "Fusion scope report does not bind the staged Phase A report and process")
    write_record(session / "work/dispatch.json", response)
    artifacts["dispatch"] = pin(session / "work/dispatch.json", "dispatch.json")
    require(sum(item["size_bytes"] for item in artifacts.values()) <= 256 * 1024 * 1024,
            "application outputs and dispatch receipt exceed 256 MiB")
    return artifacts


def dispatch(session, config):
    job = record(session / "job.json")
    options = job["job"]["options"]
    scope = plan_scope(options)
    phase = options.get("phase")
    require(job["session_version"] == 1 and phase in ("a", "b")
            and options == phase_options(scope, phase), "application job requires a phase and optional fixed scope")
    records = {"installation": config["installation"], "application": config["application"],
               "phase": phase, "claim": "unqualified_dispatch", "native_qualified": False}
    if scope is not None:
        records["scope"] = scope
    windows = windows_phase_a(config)
    if windows and (phase != "a" or scope is not None):
        return {"outcome": "waiting_application", "reason": "Windows Fusion only admits ordinary Phase A", "records": records}
    if config["application"] != "fusion" or (sys.platform != "darwin" and not windows):
        return {"outcome": "waiting_application", "reason": "this installation has no qualified Fusion fresh-phase counterpart on this platform", "records": records}
    deadline = min(job["stop_at"] - 1, time.time() + 300)
    require(deadline > time.time(), "application session has no remaining dispatch budget")
    client = None
    try:
        load_pinned(config, "re/automation/ApplicationWorkers/ApplicationProtocol.py")
        if phase == "a":
            client = QueueClient(config, deadline)
        _, raw = input_file(session, job, "plan", limit=1024 * 1024)
        plan = json.loads(raw)
        require(plan["source_revision"] == config["source_revision"] and plan_scope(plan) == scope,
                "plan and installation revision or declared scope differ")
        plan_hash = sha256(raw)
        accepted = None
        if phase == "b":
            accepted = accepted_first(session, job, config, plan_hash, scope)
            wait_for_restart(config, accepted[0]["result"]["records"], plan_hash, deadline)
            client = QueueClient(config, deadline)
        stage_plan(client, session, job, raw, plan, plan_hash, accepted)
        probe = client.call("probe", {"plan_sha256": plan_hash})
        require(probe["proof"]["control"] == "healthy" and probe["proof"]["host"] == probe["host"]
                and probe["proof"]["plan_sha256"] == plan_hash and probe["proof"]["documents_after"] == 0
                and probe["proof"].get("scope") == scope
                and 0 <= time.time() - probe["proof"]["measured_at"] <= 60, "application readiness lacks fresh pinned control evidence")
        if windows:
            proof = probe["proof"]
            require_win_sources(config, proof["loaded_sources"])
            require(proof["input_pins"] == plan["pins"]
                    and proof["readings"]["healthy_control"]["compute_all_return"] is True
                    and proof["readings"]["healthy_control"]["native_input"] == plan["pins"]["control"],
                    "Windows Fusion readiness does not bind the exact pinned control")
        probe_hash = sha256(file_bytes(client.directory / "probe.done"))
        response = client.call("phase", {"phase": phase, "plan_sha256": plan_hash,
                                         "probe_sha256": probe_hash})
        if windows:
            require(response["proof"]["probe_sha256"] == probe_hash
                    and response["proof"]["fusion_version"] == probe["proof"]["fusion_version"],
                    "Windows Fusion phase proof differs from the admitted probe")
        artifacts = collect(session, client, response, plan, plan_hash, phase)
        records.update({"plan_sha256": plan_hash, "host": response["host"], "fusion_version": response["proof"]["fusion_version"],
                        "restart_handoff": response["proof"].get("restart_handoff")})
        return {"outcome": "completed", "reason": response["reason"], "records": records, "artifacts": artifacts}
    except ApplicationTimeout as error:
        request = error.request
        link = request_link(request)
        records["queue_timeout"] = {
            "version": 1,
            "queue_job_id": link["queue_job_id"],
            "request_sha256": link["request_sha256"],
            "source_revision": request["source_revision"],
            "operation": request["operation"],
            "plan_sha256": request["body"]["plan_sha256"],
        }
        return {"outcome": "waiting_application", "reason": str(error)[:2048], "records": records}
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
