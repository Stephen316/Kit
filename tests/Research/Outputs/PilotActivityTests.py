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


# dependency timing must follow historical attempts even after the current jobs change
def CheckTiming(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    BatchPath = TmpPath / "TimingJobs.json"
    ResultPath = TmpPath / "TimingResult.json"
    RootJob = FixtureJob("timing:root", "fixture.inspect", lease_seconds=30)
    ChildJob = FixtureJob(
        "timing:child", "fixture.inspect", lease_seconds=30, depends_on=["timing:root"]
    )
    _ = BatchPath.write_text(
        JsonCodec.dumps({"jobs": [RootJob, ChildJob]}), encoding="utf-8"
    )
    _ = Client.RunCli("submit-batch", str(BatchPath))
    _ = ResultPath.write_text('{"fixture":true}', encoding="utf-8")
    for Index in range(2):
        LeasePath = TmpPath / f"TimingLease{Index}.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:timing", "--claim-file", str(LeasePath)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeasePath),
            "--result",
            str(ResultPath),
            "--outcome",
            "completed",
            "--reason",
            "completed timing fixture",
        )
    Window = ["--from-unix", "0", "--until-unix", str(TimeClock.time())]
    Pinned = ReadActivity(TmpPath, Window + ["--dependency-timing"])
    Timing = JsonCodec.loads(JsonCodec.dumps(Pinned["dependency_timing"]))
    assert Timing["settled_events"] == Timing["timed_attempts_with_ancestors"] == 2
    Chain = Timing["longest_dependency_chain"]
    assert [Entry["job"] for Entry in Chain["path"]] == ["timing:root", "timing:child"]
    assert Chain["attempt_seconds"] == sum(
        Entry["attempt_seconds"] for Entry in Chain["path"]
    )
    assert Chain["attempt_seconds"] > 0
    _ = BatchPath.write_text(
        JsonCodec.dumps({"jobs": [{**RootJob, "rule_version": "rule@2"}]}),
        encoding="utf-8",
    )
    _ = Client.RunCli("submit-batch", str(BatchPath))
    Replay = Window + [
        "--through",
        str(Pinned["through_event_id"]),
        "--dependency-timing",
    ]
    assert ReadActivity(TmpPath, Replay) == Pinned


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
    WaitReport = ReadActivity(
        RootPath,
        [
            "--from-unix",
            str(TailReport["from_unix_seconds"]),
            "--until-unix",
            str(TailReport["until_unix_seconds"]),
            "--after",
            str(Through),
            "--through",
            str(TailReport["through_event_id"]),
            "--wait-timing",
        ],
    )
    Waits = JsonCodec.loads(JsonCodec.dumps(WaitReport.pop("settlement_to_next_claim")))
    assert WaitReport == TailReport
    assert Waits["waiting_application"] == {
        "started": 1,
        "next_claim_observed": 0,
        "superseded_before_claim": 0,
        "no_next_claim_observed": 1,
        "min_seconds": None,
        "max_seconds": None,
        "total_seconds": None,
    }
    Observed = JsonCodec.loads(JsonCodec.dumps(TailReport["activity"]))
    assert Observed["resource_transitions"] == {"available": 1, "unavailable": 0}
    assert (
        Observed["claims"] == Observed["settled_outcomes"]["waiting_application"] == 1
    )


# carry in observations distinguish rearmed replaced and still parked prior jobs
def CheckCarryIn(TmpPath: FilePath) -> None:
    Client = JobClient(TmpPath)
    _ = Client.RunCli("resource", "operator:install", "--available")
    ParkCarry(Client, TmpPath, "carry:precleared", "waiting_evidence")
    ReplaceCarry(Client, TmpPath, "carry:precleared")
    ParkCarry(
        Client, TmpPath, "carry:claim", "waiting_application", ("operator:install",)
    )
    ParkCarry(Client, TmpPath, "carry:open", "waiting_evidence")
    ParkCarry(Client, TmpPath, "carry:replaced", "waiting_ci")
    Prefix = JsonCodec.loads(Client.RunCli("events", "--after", "0"))
    Begin = TimeClock.time()
    _ = Client.RunCli("resource", "operator:install", "--available")
    LeasePath = TmpPath / "RearmedLease.json"
    _ = Client.RunCli(
        "claim", "--worker", "worker:carry", "--claim-file", str(LeasePath)
    )
    ResultPath = TmpPath / "CarryResult.json"
    _ = Client.RunCli(
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(ResultPath),
        "--outcome",
        "completed",
        "--reason",
        "fixture rearmed",
    )
    ReplaceCarry(Client, TmpPath, "carry:replaced")
    ParkCarry(Client, TmpPath, "carry:new", "waiting_ci")
    Window = ["--from-unix", str(Begin), "--until-unix", str(TimeClock.time())]
    VerifyCarry(TmpPath, Client, Window, Prefix)


# a real parked controller attempt supplies each carry in fixture witness
def ParkCarry(
    Client: JobClient,
    RootPath: FilePath,
    JobName: str,
    Outcome: str,
    Resources: tuple[str, ...] = (),
) -> None:
    SubmitPath = RootPath / "CarrySubmit.json"
    LeasePath = RootPath / f"{JobName.replace(':', '-')}.json"
    ResultPath = RootPath / "CarryResult.json"
    JobInfo = FixtureJob(
        JobName, "fixture.inspect", resources=list(Resources), lease_seconds=30
    )
    _ = SubmitPath.write_text(JsonCodec.dumps(JobInfo), encoding="utf-8")
    _ = ResultPath.write_text('{"fixture":true}', encoding="utf-8")
    _ = Client.RunCli("submit", str(SubmitPath))
    _ = Client.RunCli(
        "claim", "--worker", "worker:carry", "--claim-file", str(LeasePath)
    )
    _ = Client.RunCli(
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(ResultPath),
        "--outcome",
        Outcome,
        "--reason",
        "fixture park",
    )


# changing a definition ends the old settlement without issuing a new claim
def ReplaceCarry(Client: JobClient, RootPath: FilePath, JobName: str) -> None:
    SubmitPath = RootPath / "CarrySubmit.json"
    Changed = FixtureJob(JobName, "fixture.inspect", inputs={"source": "carry:missing"})
    _ = SubmitPath.write_text(JsonCodec.dumps(Changed), encoding="utf-8")
    _ = Client.RunCli("submit", str(SubmitPath))


# the carry in section has its own evidence prefix and preserves the ordinary report
def VerifyCarry(
    RootPath: FilePath, Client: JobClient, Window: list[str], Prefix: dict[str, object]
) -> None:
    Plain = ReadActivity(RootPath, Window + ["--wait-timing"])
    Options = Window + ["--wait-timing", "--carry-in-wait-timing"]
    Pinned = ReadActivity(RootPath, Options)
    Carry = JsonCodec.loads(JsonCodec.dumps(Pinned["carry_in_wait_timing"]))
    assert {
        KeyName: Value
        for KeyName, Value in Pinned.items()
        if KeyName != "carry_in_wait_timing"
    } == Plain
    History = ReadActivity(
        RootPath,
        [
            "--from-unix",
            "0",
            "--until-unix",
            Window[1],
            "--through",
            str(Prefix["through"]),
        ],
    )
    assert Carry["prefix"] == {
        "event_count": History["selected_event_count"],
        "last_event_id": Prefix["through"],
        "events_sha256": History["selected_events_sha256"],
    }
    VerifyRows(Carry, Plain, float(Window[1]), float(Window[3]))
    Empty = ReadActivity(RootPath, Options + ["--through", str(Prefix["through"])])
    EmptyCarry = JsonCodec.loads(JsonCodec.dumps(Empty["carry_in_wait_timing"]))
    assert EmptyCarry["last_selected_event"] is None
    assert EmptyCarry["settlements"]["waiting_evidence"]["open_age_seconds"] is None
    ReplaceCarry(Client, RootPath, "carry:open")
    assert (
        ReadActivity(RootPath, Options + ["--through", str(Pinned["through_event_id"])])
        == Pinned
    )


# ages are clipped to selected clock evidence and later settlements stay in ordinary metrics
def VerifyRows(
    Carry: dict[str, object], Plain: dict[str, object], Begin: float, EndTime: float
) -> None:
    WaitRows = JsonCodec.loads(JsonCodec.dumps(Carry["settlements"]))
    LastEvent = JsonCodec.loads(JsonCodec.dumps(Carry["last_selected_event"]))
    assert (
        Carry["window_seconds_after_last_selected_event"] == EndTime - LastEvent["at"]
    )
    AppRow = WaitRows["waiting_application"]
    assert AppRow["carried_in"] == AppRow["next_claim_observed"] == 1
    assert 0 < AppRow["next_claim_total_seconds"] <= LastEvent["at"] - Begin
    Evidence = WaitRows["waiting_evidence"]
    assert Evidence["carried_in"] == Evidence["no_transition_observed"] == 1
    assert Evidence["open_age_seconds"] == LastEvent["at"] - Begin
    CiRow = WaitRows["waiting_ci"]
    assert CiRow["carried_in"] == CiRow["superseded_before_claim"] == 1
    assert CiRow["next_claim_total_seconds"] is None
    Waits = JsonCodec.loads(JsonCodec.dumps(Plain["settlement_to_next_claim"]))
    assert Waits["waiting_ci"]["started"] == 1
    assert Waits["waiting_evidence"]["started"] == 0
