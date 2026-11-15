import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from ApplicationProtocol import (
    HostQueue, MAX_BYTES, PROTOCOL, QueueClient, WaitingApplication, committed_bytes, configuration,
    encoded, file_bytes, pin, record, require, sha256, write_new, write_record,
)

WORKER = "re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py"
LAUNCHER = "re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1"
PROVIDER = "dassault.solidworks.com"
OPERATION = "p04-readback"
OUTPUTS = {
    "readback.plan": "readback/plan.json",
    "readback.measurements": "readback/measurements.json",
    "readback.receipt": "readback/receipt.json",
}


def plan_hash(config):
    return sha256(encoded({"operation": OPERATION, "source_revision": config["source_revision"]}))


def verify_sources(config):
    root = Path(__file__).resolve().parent
    for relative in (WORKER, PROTOCOL):
        require(file_bytes(root / Path(relative).name) == committed_bytes(config, relative),
                "running SolidWorks worker source differs from its installed revision")


def native_result(work, config):
    plan = file_bytes(work / OUTPUTS["readback.plan"])
    measurements = file_bytes(work / OUTPUTS["readback.measurements"], MAX_BYTES)
    receipt = record(work / OUTPUTS["readback.receipt"])
    plan_sha256 = sha256(plan)
    report = json.loads(measurements)
    run = report["run"]
    application = run["application"]
    require(json.loads(plan)["source_revision"] == config["source_revision"]
            and receipt["schema"] == 1 and receipt["status"] == "observed"
            and receipt["observed_files"] == receipt["supporting_faces_verified"] == 11
            and receipt["plan_sha256"] == report["plan_sha256"] == plan_sha256
            and receipt["measurements_sha256"] == sha256(measurements)
            and report["source_bytes_verified_after_readback"] is True
            and run["status"] == "observed" and run["owned_process_exit_observed"] is True
            and run["control_before"]["status"] == run["control_after"]["status"] == "observed"
            and application["build"] == "34.4.1.1011",
            "SOLIDWORKS readback lacks complete source, control, face or process-exit evidence")
    return {"readback_plan_sha256": plan_sha256, "solidworks_build": application["build"]}


def perform_readback(host, request, work, interop, launcher):
    expected = {"phase": OPERATION, "plan_sha256": plan_hash(host.config)}
    require(request["operation"] == "phase" and request["body"] == expected,
            "installation only accepts the pinned P04 readback phase")
    staged = work / Path(LAUNCHER).name
    write_new(staged, launcher)
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    process_environment = {key: value for key, value in os.environ.items() if key.casefold() != "psmodulepath"}
    remaining = request["deadline"] - time.time()
    require(remaining > 0, "readback request expired before native startup")
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-NonInteractive", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(staged),
         "-OutputDirectory", str(work / "readback"), "-InteropAssembly", str(interop),
         "-SourceRoot", host.config["source_root"], "-SourceRevision", host.config["source_revision"]],
        capture_output=True, env=process_environment, timeout=remaining, check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    require(result.returncode == 0, result.stderr.decode(errors="replace")[-2048:] or "SOLIDWORKS readback did not finish")
    proof = native_result(work, host.config)
    files = {role: pin(work / relative, relative) for role, relative in OUTPUTS.items()}
    return "completed", "licensed P04 readback observed all eleven captures", {
        **expected, **proof, "claim": "unqualified_application_observation",
    }, files


def listen(config, interop):
    require(os.name == "nt" and config["application"] == "solidworks", "SOLIDWORKS readback host requires Windows")
    verify_sources(config)
    launcher = committed_bytes(config, LAUNCHER)
    host = HostQueue(config, PROVIDER)
    try:
        while True:
            request = host.next_path()
            if request is None:
                time.sleep(0.05)
                continue
            host.perform(request, lambda value, work: perform_readback(host, value, work, interop, launcher))
    finally:
        host.close()


def dispatch(session, config):
    job = record(session / "job.json")
    require(job["session_version"] == 1 and job["inputs"] == {}
            and job["job"]["options"] == {"source_revision": config["source_revision"]},
            "SOLIDWORKS readback requires the installed revision and no caller-selected inputs")
    records = {"installation": config["installation"], "application": config["application"],
               "claim": "unqualified_dispatch", "native_qualified": False}
    if os.name != "nt" or config["application"] != "solidworks":
        return {"outcome": "waiting_application", "reason": "SOLIDWORKS readback requires Windows", "records": records}
    deadline = min(job["stop_at"] - 1, time.time() + 300)
    require(deadline > time.time(), "application session has no remaining dispatch budget")
    verify_sources(config)
    client = None
    try:
        client = QueueClient(config, deadline, PROVIDER)
        request = {"phase": OPERATION, "plan_sha256": plan_hash(config)}
        response = client.call("phase", request)
        proof = response["proof"]
        require(proof["claim"] == "unqualified_application_observation"
                and all(proof[key] == value for key, value in request.items())
                and {role: item["path"] for role, item in response["files"].items()} == OUTPUTS,
                "SOLIDWORKS phase proof or output roster differs from this request")
        artifacts = client.copy_files(session / "work", response)
        require(all(proof[key] == value for key, value in native_result(session / "work", config).items()),
                "copied SOLIDWORKS evidence differs from the phase proof")
        write_record(session / "work/dispatch.json", response)
        artifacts["dispatch"] = pin(session / "work/dispatch.json", "dispatch.json")
        require(sum(item["size_bytes"] for item in artifacts.values()) <= MAX_BYTES,
                "SOLIDWORKS readback artifacts and dispatch exceed the application output budget")
        records.update({**request, "host": response["host"], "solidworks_build": proof["solidworks_build"],
                        "readback_plan_sha256": proof["readback_plan_sha256"]})
        return {"outcome": "completed", "reason": response["reason"], "records": records, "artifacts": artifacts}
    except (WaitingApplication, FileNotFoundError, BlockingIOError) as error:
        return {"outcome": "waiting_application", "reason": str(error)[:2048], "records": records}
    finally:
        if client is not None:
            client.close()


def main():
    parser = argparse.ArgumentParser(description="Queue pinned SOLIDWORKS P04 readback on Windows")
    parser.add_argument("--installation", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("listen").add_argument("--interop", type=Path, required=True)
    commands.add_parser("dispatch").add_argument("session", type=Path)
    args = parser.parse_args()
    if args.command == "listen":
        try:
            listen(configuration(args.installation), args.interop.resolve(strict=True))
        except KeyboardInterrupt:
            return 0
    else:
        session = args.session.resolve(strict=True)
        try:
            result = dispatch(session, configuration(args.installation))
        except (OSError, ValueError, KeyError, TypeError) as error:
            result = {"outcome": "rejected", "reason": f"{type(error).__name__}: {error}"[:2048],
                      "records": {"claim": "unqualified_dispatch", "native_qualified": False}}
        write_record(session / "result.json", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
