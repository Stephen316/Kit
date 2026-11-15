import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryFile
import time

from ApplicationProtocol import (
    ACKNOWLEDGEMENT, ApplicationTimeout, HostQueue, MAX_BYTES, PROTOCOL, QueueClient, WaitingApplication,
    committed_bytes, configuration, encoded, file_bytes, pin, record, request_link, require, sha256, write_new, write_record,
)

WORKER = "re/automation/ApplicationWorkers/SolidWorksReadbackWorker.py"
LAUNCHER = "re/automation/PairedCaptures/SolidWorksAuthoring/ReadP04SolidWorks.ps1"
PROVIDER = "dassault.solidworks.com"
OPERATION = "p04-readback"
PRINCIPAL = "p01-p03-readback"
READBACK_SCOPES = {
    OPERATION: ("P04", "supporting_faces_verified", 11),
    PRINCIPAL: ("P01-P03", "principal_profiles_observed", 14),
}
BUILD = "34.4.1.1011"
OUTPUTS = {
    "readback.plan": "readback/plan.json",
    "readback.measurements": "readback/measurements.json",
    "readback.receipt": "readback/receipt.json",
}


class ReadbackQueue(HostQueue):
    def __init__(self, config, provider=PROVIDER, operation=OPERATION):
        self.readback_operation = operation
        super().__init__(config, provider)

    def fenced(self):
        return os.path.lexists(self.root / "fence.json") or os.path.lexists(self.root / ACKNOWLEDGEMENT)


def plan_hash(config, operation=OPERATION):
    return sha256(encoded({"operation": operation, "source_revision": config["source_revision"]}))


def phase_request(config, operation):
    return {"phase": operation, "plan_sha256": plan_hash(config, operation)}


def verify_sources(config):
    root = Path(__file__).resolve().parent
    for relative in (WORKER, PROTOCOL):
        require(file_bytes(root / Path(relative).name) == committed_bytes(config, relative),
                "running SolidWorks worker source differs from its installed revision")


def native_result(work, config, operation=OPERATION):
    scope, count_field, count = READBACK_SCOPES[operation]
    plan_bytes = file_bytes(work / OUTPUTS["readback.plan"])
    plan = json.loads(plan_bytes)
    measurements = file_bytes(work / OUTPUTS["readback.measurements"], MAX_BYTES)
    receipt = record(work / OUTPUTS["readback.receipt"])
    plan_sha256 = sha256(plan_bytes)
    report = json.loads(measurements)
    run = report["run"]
    application = run["application"]
    owner = run["native_owner"]
    require(plan["source_revision"] == config["source_revision"] and plan["recipe"] == scope
            and receipt["schema"] == 1 and receipt["status"] == "observed"
            and receipt["observed_files"] == receipt[count_field] == count
            and len(run["observations"]) == count
            and set(plan["native_files"]) == {item["file"] for item in run["observations"]}
            and all(item["status"] == "observed" for item in run["observations"])
            and receipt["plan_sha256"] == report["plan_sha256"] == plan_sha256
            and receipt["measurements_sha256"] == sha256(measurements)
            and report["source_bytes_verified_after_readback"] is True
            and run["status"] == "observed" and run["owned_process_exit_observed"] is True
            and run["control_before"]["status"] == run["control_after"]["status"] == "observed"
            and application["build"] == owner["build"] == BUILD
            and owner["source_revision"] == config["source_revision"] and owner["initial_documents"] == 0,
            "SOLIDWORKS readback lacks complete source, control, profile or process-exit evidence")
    return {"readback_plan_sha256": plan_sha256, "solidworks_build": application["build"],
            "native_owner_sha256": sha256(encoded(owner))}


def session_id(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel.ProcessIdToSessionId
    query.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    query.restype = wintypes.BOOL
    result = wintypes.DWORD()
    if not query(pid, ctypes.byref(result)):
        raise ctypes.WinError(ctypes.get_last_error())
    return result.value


def native_identity(handle):
    from WindowsIdentity import creation_time

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_pid = kernel.GetProcessId
    get_pid.argtypes = [wintypes.HANDLE]
    get_pid.restype = wintypes.DWORD
    pid = get_pid(int(handle))
    if not pid:
        raise ctypes.WinError(ctypes.get_last_error())
    image_query = kernel.QueryFullProcessImageNameW
    image_query.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    image_query.restype = wintypes.BOOL
    buffer = ctypes.create_unicode_buffer(32768)
    size = wintypes.DWORD(len(buffer))
    if not image_query(int(handle), 0, buffer, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"pid": pid, "created": creation_time(int(handle)), "session": session_id(pid),
            "image": str(Path(buffer.value).resolve(strict=True))}


def registered_executable():
    from winreg import HKEY_CLASSES_ROOT, KEY_READ, KEY_WOW64_64KEY, OpenKey, QueryValue

    access = KEY_READ | KEY_WOW64_64KEY
    with OpenKey(HKEY_CLASSES_ROOT, r"SldWorks.Application\CLSID", 0, access) as registration:
        clsid = QueryValue(registration, None)
    with OpenKey(HKEY_CLASSES_ROOT, fr"CLSID\{clsid}\LocalServer32", 0, access) as server:
        return Path(QueryValue(server, None)).resolve(strict=True)


def launch_solidworks(executable):
    import win32process

    startup = win32process.STARTUPINFO()
    startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    handle, thread, _, _ = win32process.CreateProcess(
        str(executable), subprocess.list2cmdline([str(executable)]), None, None, False, 0,
        None, str(executable.parent), startup,
    )
    thread.Close()
    return handle


def launch_readiness(path, collector, deadline):
    while time.time() < deadline:
        try:
            return record(path)
        except FileNotFoundError:
            if collector.poll() is not None:
                return None
            time.sleep(0.05)
    raise subprocess.TimeoutExpired("SOLIDWORKS launcher preflight", 0)


def ready_executable(ready, request_pin):
    require(set(ready) == {*request_pin, "executable", "executable_sha256"}
            and all(ready[key] == value for key, value in request_pin.items())
            and isinstance(ready["executable"], str), "SOLIDWORKS preflight differs from the queued request")
    executable = registered_executable()
    require(executable.name.casefold() == "sldworks.exe" and Path(ready["executable"]).resolve(strict=True) == executable
            and sha256(file_bytes(executable, MAX_BYTES)) == ready["executable_sha256"],
            "SOLIDWORKS preflight differs from the installed executable")
    return executable


def verify_native_ticket(path, launch):
    expected = {**launch, "build": BUILD, "initial_documents": 0}
    require(encoded(record(path)) == encoded(expected),
            "SOLIDWORKS collector did not ticket the exact owned scratch installation")
    return sha256(encoded(expected))


def stop_collector(collector):
    if collector.poll() is None:
        collector.kill()
        collector.wait(timeout=5)


def recover_owned_process(handle, launch, ticket, deadline=None):
    import pywintypes
    import win32event
    import win32process

    ticket_hash = verify_native_ticket(ticket, launch)
    status = win32event.WaitForSingleObject(handle, 0)
    if status == win32event.WAIT_OBJECT_0:
        return "already_exited", ticket_hash
    require(status == win32event.WAIT_TIMEOUT, "owned process wait did not report a live identity")
    expected = {key: launch[key] for key in ("pid", "created", "session", "image")}
    require(native_identity(handle) == expected and expected["session"] == session_id(os.getpid()),
            "held SOLIDWORKS process identity changed before recovery")
    wait_ms = 5000 if deadline is None else min(5000, int((deadline - time.time()) * 1000))
    require(wait_ms > 0, "collector deadline expired before owned process recovery")
    try:
        win32process.TerminateProcess(handle, 1)
    except pywintypes.error:
        if win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_OBJECT_0:
            return "already_exited", ticket_hash
        raise
    if deadline is not None:
        wait_ms = max(0, min(wait_ms, int((deadline - time.time()) * 1000)))
    require(win32event.WaitForSingleObject(handle, wait_ms) == win32event.WAIT_OBJECT_0,
            "termination did not signal the held SOLIDWORKS process")
    return "terminated_owned_process", ticket_hash


def new_recovery(request, listener, trigger):
    return {
        "version": 2, "installation": request["installation"], "source_revision": request["source_revision"],
        **request_link(request), "listener": listener, "trigger": trigger, "status": "quarantined",
    }


def update_owned_recovery(work, recovery, handle, launch, deadline=None):
    require(launch["request_sha256"] == recovery["request_sha256"]
            and launch["source_revision"] == recovery["source_revision"],
            "held SOLIDWORKS launch belongs to a different request")
    recovery["status"], recovery["owner_ticket_sha256"] = recover_owned_process(
        handle, launch, work / "readback/native-owner.json", deadline,
    )
    recovery["pid"] = launch["pid"]
    recovery["created"] = launch["created"]


def record_timeout(work, request, listener, collector, handle, launch, recovery_enabled):
    recovery = new_recovery(request, listener, "collector_timeout")
    try:
        stop_collector(collector)
        if not recovery_enabled:
            recovery["reason"] = "automatic timeout termination is disabled for this listener"
        elif handle is None or launch is None:
            recovery["reason"] = "no retained direct launch identity"
        else:
            update_owned_recovery(work, recovery, handle, launch)
    except Exception as error:
        recovery["reason"] = f"{type(error).__name__}: {error}"[:2048]
    write_record(work / "native-timeout-request.json", request)
    write_record(work / "native-recovery.json", recovery)


def record_collector_failure(work, request, listener, collector, handle, launch):
    recovery = new_recovery(request, listener, "collector_failure")
    try:
        return_code = collector.poll()
        require(return_code is not None, "collector has not exited")
        recovery["collector_return_code"] = return_code
        update_owned_recovery(work, recovery, handle, launch, request["deadline"])
    except Exception as error:
        recovery["reason"] = f"{type(error).__name__}: {error}"[:2048]
    write_record(work / "native-failure-recovery.json", recovery)


def run_collector(host, request, work, interop, staged, recovery_enabled, recover_failure):
    operation = host.readback_operation
    scope, _, _ = READBACK_SCOPES[operation]
    expected = phase_request(host.config, operation)
    require(request["operation"] == "phase" and request["body"] == expected,
            "installation only accepts its pinned SOLIDWORKS readback phase")
    import win32event

    output = work / "readback"
    request_pin = {"version": 1, "request_sha256": sha256(encoded(request)),
                   "source_revision": host.config["source_revision"]}
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    process_environment = {key: value for key, value in os.environ.items() if key.casefold() != "psmodulepath"}
    deadline = request["deadline"]
    require(deadline > time.time(), "readback request expired before collector startup")
    with TemporaryFile() as errors:
        collector = subprocess.Popen(
            [str(powershell), "-NoProfile", "-NonInteractive", "-STA", "-ExecutionPolicy", "Bypass", "-File", str(staged),
             "-OutputDirectory", str(output), "-InteropAssembly", str(interop),
             "-SourceRoot", host.config["source_root"], "-SourceRevision", host.config["source_revision"],
             "-QueuedRequestSha256", request_pin["request_sha256"], "-ReadbackScope", scope],
            stdout=subprocess.DEVNULL, stderr=errors, env=process_environment, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        handle, launch = None, None
        try:
            ready = launch_readiness(output / "native-ready.json", collector, deadline)
            if ready is not None:
                executable = ready_executable(ready, request_pin)
                require(time.time() < deadline and collector.poll() is None and not os.path.lexists(work / "cancel.json"),
                        "readback request expired before native startup")
                handle = launch_solidworks(executable)
                identity = native_identity(handle)
                require(Path(identity["image"]) == executable and identity["session"] == session_id(os.getpid()),
                        "direct launch did not enter the registered installation and desktop session")
                launch = {**request_pin, **identity}
                write_record(output / "native-launch.json", launch)
            status = collector.wait(timeout=max(0, deadline - time.time()))
            errors.seek(0, os.SEEK_END)
            errors.seek(max(0, errors.tell() - 2048))
            require(status == 0, errors.read().decode(errors="replace") or "SOLIDWORKS readback did not finish")
            require(handle is not None, "SOLIDWORKS collector completed without a directly owned process")
            owner_hash = verify_native_ticket(output / "native-owner.json", launch)
            require(win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_OBJECT_0,
                    "SOLIDWORKS collector did not close the directly owned process")
            return owner_hash
        except subprocess.TimeoutExpired:
            record_timeout(work, request, host.host, collector, handle, launch, recovery_enabled)
            raise
        except Exception as error:
            if recover_failure and handle is not None and launch is not None:
                try:
                    record_collector_failure(work, request, host.host, collector, handle, launch)
                except (OSError, ValueError) as retention_error:
                    raise WaitingApplication(
                        f"{error}; native failure evidence could not be retained ({type(retention_error).__name__})"
                    ) from error
            raise
        finally:
            try:
                stop_collector(collector)
            finally:
                if handle is not None:
                    handle.Close()


def perform_readback(host, request, work, interop, launcher, recovery_enabled, recover_failure):
    operation = host.readback_operation
    expected = phase_request(host.config, operation)
    staged = work / Path(LAUNCHER).name
    write_new(staged, launcher)
    owner_hash = run_collector(host, request, work, interop, staged, recovery_enabled, recover_failure)
    proof = native_result(work, host.config, operation)
    require(proof["native_owner_sha256"] == owner_hash, "SOLIDWORKS measurements do not preserve the verified ownership ticket")
    files = {role: pin(work / relative, relative) for role, relative in OUTPUTS.items()}
    return "completed", f"licensed {READBACK_SCOPES[operation][0]} readback observed all pinned captures", {
        **expected, **proof, "claim": "unqualified_application_observation",
    }, files


def listen(config, interop, recovery_enabled, recover_failure, operation=OPERATION):
    require(os.name == "nt" and config["application"] == "solidworks", "SOLIDWORKS readback host requires Windows")
    verify_sources(config)
    launcher = committed_bytes(config, LAUNCHER)
    host = ReadbackQueue(config, PROVIDER, operation)
    try:
        while True:
            request = host.next_path()
            if request is None:
                time.sleep(0.05)
                continue
            host.perform(request, lambda value, work: perform_readback(
                host, value, work, interop, launcher, recovery_enabled, recover_failure,
            ))
    finally:
        host.close()


def dispatch(session, config, operation=OPERATION):
    job = record(session / "job.json")
    options = {"source_revision": config["source_revision"]}
    if operation == PRINCIPAL:
        options["readback_operation"] = PRINCIPAL
    require(job["session_version"] == 1 and job["inputs"] == {}
            and job["job"]["options"] == options,
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
        request = phase_request(config, operation)
        response = client.call("phase", request)
        proof = response["proof"]
        require(proof["claim"] == "unqualified_application_observation"
                and all(proof[key] == value for key, value in request.items())
                and {role: item["path"] for role, item in response["files"].items()} == OUTPUTS,
                "SOLIDWORKS phase proof or output roster differs from this request")
        artifacts = client.copy_files(session / "work", response)
        require(all(proof[key] == value for key, value in native_result(session / "work", config, operation).items()),
                "copied SOLIDWORKS evidence differs from the phase proof")
        write_record(session / "work/dispatch.json", response)
        artifacts["dispatch"] = pin(session / "work/dispatch.json", "dispatch.json")
        require(sum(item["size_bytes"] for item in artifacts.values()) <= MAX_BYTES,
                "SOLIDWORKS readback artifacts and dispatch exceed the application output budget")
        records.update({**request, "host": response["host"], "solidworks_build": proof["solidworks_build"],
                        "readback_plan_sha256": proof["readback_plan_sha256"]})
        return {"outcome": "completed", "reason": response["reason"], "records": records, "artifacts": artifacts}
    except ApplicationTimeout as error:
        records["queue_timeout"] = {
            "version": 1, **request_link(error.request), "installation": config["installation"],
            "source_revision": config["source_revision"],
            "job_id": job["job"]["id"], "kind": job["job"]["kind"], "resources": job["job"]["resources"],
            "session": job["session"], "generation": job["generation"], "fingerprint": job["fingerprint"],
            "attempt": job["attempt"],
        }
        return {"outcome": "waiting_application", "reason": str(error)[:2048], "records": records}
    except (WaitingApplication, FileNotFoundError, BlockingIOError) as error:
        return {"outcome": "waiting_application", "reason": str(error)[:2048], "records": records}
    finally:
        if client is not None:
            client.close()


def main():
    parser = argparse.ArgumentParser(description="Queue pinned SOLIDWORKS discovery readback on Windows")
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--readback-operation", choices=tuple(READBACK_SCOPES), default=OPERATION)
    commands = parser.add_subparsers(dest="command", required=True)
    listener = commands.add_parser("listen")
    listener.add_argument("--interop", type=Path, required=True)
    listener.add_argument("--recover-owned-timeout", action="store_true")
    listener.add_argument("--recover-owned-failure", action="store_true")
    commands.add_parser("dispatch").add_argument("session", type=Path)
    args = parser.parse_args()
    if args.command == "listen":
        try:
            listen(configuration(args.installation), args.interop.resolve(strict=True),
                   args.recover_owned_timeout, args.recover_owned_failure, args.readback_operation)
        except KeyboardInterrupt:
            return 0
    else:
        session = args.session.resolve(strict=True)
        try:
            result = dispatch(session, configuration(args.installation), args.readback_operation)
        except (OSError, ValueError, KeyError, TypeError) as error:
            result = {"outcome": "rejected", "reason": f"{type(error).__name__}: {error}"[:2048],
                      "records": {"claim": "unqualified_dispatch", "native_qualified": False}}
        write_record(session / "result.json", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
