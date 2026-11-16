import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from ApplicationWorkers.ApplicationProtocol import directory, encoded, windows_git, write_new, write_record
from LogCapture import LogCapture
from Processes import KILL_SIGNAL
from Records import bounded


ROOT = Path(__file__).resolve().parents[2]
SCOPE = "two-body-through-all-discovery"
SOURCE = Path("re/automation/PairedCaptures/ScopeControl")
LAUNCHER = SOURCE / "RunSolidWorksScope.ps1"
SOURCES = {
    "watchdog": Path("re/automation/ScopeWatchdog.py"),
    "launcher": LAUNCHER,
    "collector": SOURCE / "SolidWorksScopeControl.cs",
    "specification": SOURCE / "ScopeControlSpec.json",
    "job_owner": Path("re/automation/WindowsProcess.py"),
    "job_launch": Path("re/automation/WindowsApi.py"),
    "job_members": Path("re/automation/WindowsJobMembers.py"),
    "process_identity": Path("re/automation/ApplicationWorkers/WindowsIdentity.py"),
    "records": Path("re/automation/ApplicationWorkers/WindowsRecords.py"),
    "publication": Path("re/automation/ApplicationWorkers/ApplicationProtocol.py"),
    "logs": Path("re/automation/LogCapture.py"),
}
LOG_LIMIT = 1024 * 1024


# windows startup is pinned to the same checkout as the native control specification
def source_pins(revision):
    from ApplicationWorkers.WindowsRecords import open_record

    git = [windows_git(), "--no-replace-objects", "-C", str(ROOT)]
    head = subprocess.check_output([*git, "rev-parse", "--verify", "HEAD^{commit}"], timeout=15).strip()
    if head != revision.encode("ascii"):
        raise ValueError("scope checkout differs from the requested revision")
    pins = {}
    for role, path in SOURCES.items():
        expected = subprocess.check_output([*git, "show", f"{revision}:{path.as_posix()}"], timeout=15)
        with open_record(ROOT / path) as source:
            content = source.read(LOG_LIMIT + 1)
        if not 0 < len(content) <= LOG_LIMIT or content != expected:
            raise ValueError(f"scope source differs from Git: {path.as_posix()}")
        pins[role] = {
            "path": path.as_posix(), "sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content),
        }
    return pins


# a successful process exit must still seal the exact report returned by the pinned collector
def completed_report(path, provenance):
    from ApplicationWorkers.WindowsRecords import open_record

    with open_record(path) as source:
        raw = source.read(LOG_LIMIT + 1)
    if len(raw) > LOG_LIMIT:
        raise ValueError("scope report exceeds its byte limit")
    report = json.loads(raw)
    if (report["schema"] != 1 or report["scope"] != SCOPE or report["application"] != "solidworks"
            or report["source_revision"] != provenance["source_revision"]
            or [case["mode"] for case in report["cases"]] != ["automatic", "explicit_a", "explicit_ab"]
            or any(report["native_processes"][phase]["exited_observed"] is not True for phase in ("authoring", "reopen"))):
        raise ValueError("scope report does not match the watched revision and campaign")
    return {"path": "scope/report.json", "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


# job membership supplies the stop authority even when the collector blocks inside a native call
def drain_job(process, receipt):
    from WindowsJobMembers import observed_members

    if process.poll() is None:
        try:
            receipt["members_before_stop"] = observed_members(process.job)
        except OSError:
            receipt["members_before_stop"] = None
        process.signal(KILL_SIGNAL)
        process.wait(timeout=5)
    observed = process.finish()
    if observed is None:
        raise ValueError("the owned campaign did not finish")
    receipt["exit_status"] = observed["exit_status"]
    receipt["job_drained"] = True


# the watchdog remains outside its own kill boundary so it can retain terminal evidence
def watch(command, root, environment, run, seconds, provenance, *, report_path=None):
    receipt = {
        "schema": 1, **provenance, "timeout_seconds": seconds, "started_at": time.time(),
        "outcome": "failed", "job_drained": None, "exit_status": None, "logs": {},
    }
    deadline = time.monotonic() + seconds
    process = None
    captures = {}
    try:
        from WindowsProcess import WindowsProcess

        for name in ("stdout", "stderr"):
            captures[name] = LogCapture(run / f"{name}.log", LOG_LIMIT)
        process = WindowsProcess(command, root, environment, captures["stdout"].writer, captures["stderr"].writer)
        receipt["collector"] = {"pid": process.pid, "started": process.identity, "job_object": process.job_name}
        receipt["job_drained"] = False
        launch = encoded({**receipt, "outcome": "running"})
        write_new(run / "launch.json", launch)
        receipt["launch_sha256"] = hashlib.sha256(launch).hexdigest()
        for log in captures.values():
            log.close_writer()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                receipt["outcome"] = "timed_out"
                break
            if process.poll() is not None:
                if process.returncode == 0:
                    receipt["outcome"] = "completed"
                break
            for log in captures.values():
                log.drain()
            time.sleep(min(remaining, 0.05))
    except KeyboardInterrupt:
        receipt["outcome"] = "interrupted"
    except Exception as error:
        receipt["error"] = f"{type(error).__name__}: {error}"[:2048]
    finally:
        if process is not None:
            try:
                drain_job(process, receipt)
            except Exception as error:
                receipt["drain_error"] = f"{type(error).__name__}: {error}"[:2048]
            finally:
                try:
                    process.close()
                except Exception as error:
                    receipt["close_error"] = f"{type(error).__name__}: {error}"[:2048]
        for log in captures.values():
            try:
                log.close()
            except OSError as error:
                receipt["log_error"] = f"{type(error).__name__}: {error}"[:2048]
        receipt["logs"] = {name: log.receipt() for name, log in captures.items()}
    if receipt["outcome"] == "completed" and (receipt["job_drained"] is not True or "close_error" in receipt):
        receipt["outcome"] = "failed"
    if receipt["outcome"] == "completed" and report_path is not None:
        try:
            receipt["report"] = completed_report(report_path, provenance)
        except (OSError, ValueError, TypeError, KeyError) as error:
            receipt["outcome"] = "failed"
            receipt["error"] = f"{type(error).__name__}: {error}"[:2048]
    receipt["finished_at"] = time.time()
    write_record(run / "watchdog.json", receipt)
    return receipt


# the public entry point offers only the fixed signed in scope collection command
def main():
    parser = argparse.ArgumentParser(description="Bound the licensed standalone SOLIDWORKS scope capture")
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    args = parser.parse_args()
    try:
        if sys.platform != "win32" or not re.fullmatch("[0-9a-f]{40}", args.source_revision):
            raise ValueError("scope watchdog requires Windows and a full Git revision")
        seconds = bounded(args.timeout_seconds, 1, 86400)
        pins = source_pins(args.source_revision)
        run = Path(os.path.abspath(args.output_directory))
        if run == ROOT or ROOT in run.parents or run.anchor.startswith("\\\\"):
            raise ValueError("choose a new local output directory outside the checkout")
        directory(run.parent)
        run.mkdir(mode=0o700)
        output = run / "scope"
        powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        command = [
            str(powershell), "-NoProfile", "-NonInteractive", "-STA", "-File", str(ROOT / LAUNCHER),
            "-OutputDirectory", str(output), "-SourceRevision", args.source_revision,
        ]
        environment = {key: value for key, value in os.environ.items() if key.casefold() != "psmodulepath"}
        provenance = {"scope": SCOPE, "source_revision": args.source_revision, "sources": pins}
        receipt = watch(command, ROOT, environment, run, seconds, provenance, report_path=output / "report.json")
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"scope watchdog: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"outcome": receipt["outcome"], "job_drained": receipt["job_drained"]}))
    if receipt["job_drained"] is not True:
        return 1
    return {"completed": 0, "timed_out": 124, "interrupted": 130}.get(receipt["outcome"], 1)


if __name__ == "__main__":
    sys.exit(main())
