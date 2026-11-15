import json as JsonCodec
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient
from tests.Research.SupervisorClient import FixtureJob, KRepoRoot


# the reporter crosses a page boundary while preserving its first visible event cutoff
def CheckPilot(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    BatchPath = TmpPath / "EventJobs.json"
    Entries = [
        FixtureJob(f"observe:{Index}", "fixture.inspect", lease_seconds=30)
        for Index in range(101)
    ]
    _ = BatchPath.write_text(JsonCodec.dumps({"jobs": Entries}), encoding="utf-8")
    _ = Client.RunCli("submit-batch", str(BatchPath))
    PageInfo = JsonCodec.loads(Client.RunCli("events", "--after", "0"))
    assert PageInfo["next_after"] == 100
    _ = Client.RunCli("resource", "operator:available", "--available")
    VerifyPilot(TmpPath, Client, PageInfo["through"])


# the activity reporter reads existing evidence without changing controller bytes
def ReadActivity(RootPath: FilePath, Arguments: list[str]) -> dict[str, object]:
    StorePath = RootPath / "State"
    DatabasePath = StorePath / "ledger.sqlite3"
    Before = DatabasePath.read_bytes()
    Program = KRepoRoot / "re/automation/PilotActivity.py"
    Process = Subprocess.run(
        [System.executable, str(Program), "--store", str(StorePath), *Arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 0, Process.stderr
    assert DatabasePath.read_bytes() == Before
    Report: dict[str, object] = JsonCodec.loads(Process.stdout)
    return Report


# a recorded blocker needs a real claim and terminal application parking event
def RecordParking(Client: JobClient, RootPath: FilePath) -> None:
    LeasePath = RootPath / "PilotLease.json"
    ResultPath = RootPath / "PilotResult.json"
    _ = ResultPath.write_text('{"fixture":true}', encoding="utf-8")
    _ = Client.RunCli(
        "claim", "--worker", "worker:pre-pilot", "--claim-file", str(LeasePath)
    )
    _ = Client.RunCli(
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(ResultPath),
        "--outcome",
        "waiting_application",
        "--reason",
        "fixture installation unavailable",
    )


# exact cutoffs make the same pilot evidence reproducible after later operating events
def VerifyPilot(RootPath: FilePath, Client: JobClient, Through: int) -> None:
    Window = ["--from-unix", "0", "--until-unix", str(TimeClock.time())]
    Arguments = Window + ["--through", str(Through)]
    Pinned = ReadActivity(RootPath, Arguments)
    Activity = JsonCodec.loads(JsonCodec.dumps(Pinned["activity"]))
    assert Pinned["scope"] == "a03_controller_pre_pilot_activity"
    assert Pinned["scanned_event_count"] == Pinned["selected_event_count"] == Through
    assert Activity["submission_events"] == 101
    assert Activity["resource_transitions"] == {"available": 0, "unavailable": 0}
    Latest = ReadActivity(RootPath, Window)
    assert Latest["through_event_id"] == Through + 1
    assert Latest["selected_events_sha256"] != Pinned["selected_events_sha256"]
    RecordParking(Client, RootPath)
    assert ReadActivity(RootPath, Arguments) == Pinned
    TailReport = ReadActivity(
        RootPath,
        [
            "--from-unix",
            "0",
            "--until-unix",
            str(TimeClock.time()),
            "--after",
            str(Through),
        ],
    )
    Observed = JsonCodec.loads(JsonCodec.dumps(TailReport["activity"]))
    assert Observed["resource_transitions"] == {"available": 1, "unavailable": 0}
    assert (
        Observed["claims"] == Observed["settled_outcomes"]["waiting_application"] == 1
    )
