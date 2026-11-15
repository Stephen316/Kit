import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, KRepoRoot, SessionHost


# the rearm fixture needs a bound terminal queue record and a real disposable process handle
def RearmListener(Queue: DispatchHost, Operation: str) -> "Subprocess.Popen[str]":
    PathValue = Queue.RootPath / "RearmFixture.py"
    _ = PathValue.write_text(
        """import os
import subprocess
import sys
import time
from pathlib import Path
import win32event
import win32process

sys.path.insert(0, sys.argv[1])
from ApplicationProtocol import configuration, encoded, sha256, write_record
from SolidWorksReadbackWorker import BUILD, PROVIDER, ReadbackQueue, native_identity, phase_request, record_timeout

config = configuration(Path(sys.argv[2]))
operation = sys.argv[3]
host = ReadbackQueue(config, PROVIDER, operation)
exe = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
def args(script):
    return [exe, '-NoProfile', '-NonInteractive', '-Command', script]

def fixture(value, work):
    assert value["body"] == phase_request(config, operation)
    output = work / 'readback'
    output.mkdir()
    child, thread, _, _ = win32process.CreateProcess(
        exe, subprocess.list2cmdline(args('Start-Sleep -Seconds 45')), None, None,
        False, subprocess.CREATE_NO_WINDOW, None, str(work), win32process.STARTUPINFO(),
    )
    thread.Close()
    try:
        launch = {'version': 1, 'request_sha256': sha256(encoded(value)),
                  'source_revision': config['source_revision'], **native_identity(child)}
        write_record(output / 'native-launch.json', launch)
        write_record(output / 'native-owner.json', {**launch, 'build': BUILD, 'initial_documents': 0})
        while time.time() < value['deadline'] + 0.25:
            time.sleep(0.05)
        win32process.TerminateProcess(child, 0)
        assert win32event.WaitForSingleObject(child, 5000) == win32event.WAIT_OBJECT_0
        with subprocess.Popen(args('exit 0'), creationflags=subprocess.CREATE_NO_WINDOW) as collector:
            assert collector.wait(timeout=10) == 0
            record_timeout(work, value, host.host, collector, child, launch, True)
        return 'waiting_application', 'fixture application deadline', None, None
    finally:
        if win32event.WaitForSingleObject(child, 0) == win32event.WAIT_TIMEOUT:
            win32process.TerminateProcess(child, 1)
            assert win32event.WaitForSingleObject(child, 5000) == win32event.WAIT_OBJECT_0
        child.Close()

try:
    write_record(host.root / 'ready.json', {'host': host.host})
    while not (host.root / 'stop-fixture').exists():
        request = host.next_path()
        if request is None:
            time.sleep(0.05)
        else:
            host.perform(request, fixture)
finally:
    host.close()
""",
        encoding="utf-8",
    )
    return Subprocess.Popen(
        [
            System.executable,
            str(PathValue),
            str(KRepoRoot / "re/automation/ApplicationWorkers"),
            str(Queue.ConfigFile),
            Operation,
        ],
        stdout=Subprocess.PIPE,
        stderr=Subprocess.PIPE,
        text=True,
    )


# the real supervisor must consume the original attempt budget and retain both failed spools
@TestMark.skipif(OsLayer.name != "nt", reason="requires Windows application transport")
@TestMark.parametrize(
    ("Restart", "Operation"),
    ((False, "p04-readback"), (True, "p04-readback"), (False, "p01-p03-readback")),
)
def CheckRearm(Restart: bool, Operation: str) -> None:
    with TempFiles.TemporaryDirectory() as TempName:
        RootPath = FilePath(TempName).resolve()
        Queue = DispatchHost(RootPath)
        Config = JsonCodec.loads(Queue.ConfigFile.read_bytes())
        Config["application"] = "solidworks"
        _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
        Harness = SessionHost(RootPath, {"apps": 1}, {"fixture.app": "apps"})
        SetAppRunner(Harness, Queue.ConfigFile, Readback=True)
        RegistryPath = RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryPath.read_bytes())
        Runner = Registry["runners"]["fixture.app"]
        Runner["application_installation"] = str(Queue.ConfigFile)
        if Operation != "p04-readback":
            Runner["argv"][-2:-2] = ["--readback-operation", Operation]
        _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
        Listener = RearmListener(Queue, Operation)
        try:
            _ = Queue.WaitFile("ready.json")
            Options = {"source_revision": str(Config["source_revision"])}
            if Operation != "p04-readback":
                Options["readback_operation"] = Operation
            RunRetries(Harness, Options, Restart)
            AssertSpools(Queue)
        finally:
            (Queue.Endpoint / "stop-fixture").touch()
            Output, ErrorText = Listener.communicate(timeout=35)
            assert Listener.returncode == 0, Output + ErrorText


# a successful rearm must issue only the next configured attempt without erasing the first result
def RunRetries(Harness: SessionHost, Options: dict[str, str], Restart: bool) -> None:
    Harness.SubmitJobs(
        [
            FixtureJob(
                "fixture:rearm",
                "fixture.app",
                lease_seconds=12,
                timeout_seconds=15,
                max_attempts=2,
                retry_base_seconds=1,
                resources=["application:missing"],
                options={**Options},
            )
        ]
    )
    if Restart:
        CrashAfterPark(Harness)
    Events = [
        CastValue(dict[str, object], Event)
        for Event in Harness.RunIdle(IdleSeconds=3, MaxSeconds=65)
    ]
    (Rearmed,) = tuple(
        Event for Event in Events if Event.get("event") == "application_rearm"
    )
    assert Rearmed["attempt"] == 1 and Rearmed["status"] == "rearmed"
    assert Rearmed["recovered"] is Restart
    (Refused,) = tuple(
        Event for Event in Events if Event.get("event") == "application_rearm_failed"
    )
    assert Refused["attempt"] == 2 and "retry budget" in str(Refused["error"])
    Final = Harness.ReadJob("fixture:rearm")
    assert Final["state"] == "waiting_application" and Final["attempts"] == 2
    assert Harness.StorePath is not None
    Digest = str(Rearmed["archive"])
    Manifest = JsonCodec.loads(
        (Harness.StorePath / "objects" / Digest[:2] / Digest).read_bytes()
    )
    assert Manifest["claim"]["attempt"] == 1 and Manifest["receipt"] != Final["receipt"]
    assert "native-recovery.json" in Manifest["files"]


# the replacement owner must see the real accepted failure after the old process dies
def CrashAfterPark(Harness: SessionHost) -> None:
    Wrapper = Harness.RootPath / "CrashAfterPark.py"
    _ = Wrapper.write_text(
        """import os
import sys
sys.path.insert(0, sys.argv.pop(1))
from Adapters import A03Adapter
from Supervisor import main

finish = A03Adapter.FinishJob
def interrupt(self, path, outcome, result, reason):
    response = finish(self, path, outcome, result, reason)
    if outcome == 'waiting_application' and response['stale'] is False:
        os._exit(71)
    return response

A03Adapter.FinishJob = interrupt
sys.exit(main())
""",
        encoding="utf-8",
    )
    Original = Subprocess.run(
        [
            System.executable,
            str(Wrapper),
            str(KRepoRoot / "re/automation"),
            "--config",
            str(Harness.ConfigFile),
            "run",
            "--idle-seconds",
            "3",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Original.returncode == 71, Original.stdout + Original.stderr
    JobInfo = Harness.ReadJob("fixture:rearm")
    assert JobInfo["state"] == "waiting_application" and JobInfo["attempts"] == 1
    (IntentPath,) = (Harness.RootPath / "SupervisorState/application-rearms").glob(
        "*.json"
    )
    assert IntentPath.is_file()
    assert "application_rearm_intent_sha256" in Harness.ReadResult("fixture:rearm")


# confirmed cleanup must preserve the archived first spool and the exhausted attempt quarantine
def AssertSpools(Queue: DispatchHost) -> None:
    (Archived,) = (Queue.Endpoint / "failed-spools").iterdir()
    (Active,) = (Queue.Endpoint / "jobs").iterdir()
    _ = Queue.WaitFile((Active / "phase.done").relative_to(Queue.Endpoint).as_posix())
    Fence = JsonCodec.loads((Queue.Endpoint / "fence.json").read_bytes())
    assert Archived.name != Active.name and Fence["job_id"] == Active.name
    assert (Archived / "native-timeout-request.json").is_file()
    assert (Active / "native-timeout-request.json").is_file()
