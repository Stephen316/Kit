import hashlib as Hashing
import json as JsonCodec
import os as OsLayer
import sqlite3 as SqlLayer
import subprocess as Subprocess
import sys as System
from contextlib import closing as CloseResource
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.SetAppRunner import SetAppRunner
from tests.Research.SupervisorClient import FixtureJob, KRepoRoot, SessionHost


# a real controller must retain the identity of the timed out request before any recovery is considered
@TestMark.skipif(OsLayer.name != "nt", reason="requires Windows application transport")
def CheckTimedLink(TmpPath: FilePath) -> None:
    Harness, Queue = PrepareTimeout(TmpPath.resolve(), 15)
    Events = Harness.RunIdle()
    AssertFirstWait(Events)
    (Spool,) = (Queue.Endpoint / "jobs").iterdir()
    AssertTimedLink(Harness, Spool)
    FencePath = Queue.Endpoint / "fence.json"
    Request = JsonCodec.loads((Spool / "phase.request").read_bytes())
    Cancel = JsonCodec.loads((Spool / "cancel.json").read_bytes())
    Fence = JsonCodec.loads(FencePath.read_bytes())
    assert Cancel["reason"] == "requesting worker stopped before application completion"
    assert Request["deadline"] <= Cancel["at"] <= Fence["at"]
    assert not (Spool / "native-recovery.json").exists()
    AssertEpoch(Harness)


# a failed publication needs a parked controller job and its retained request spool
@TestMark.skipif(OsLayer.name != "nt", reason="requires Windows application transport")
def CheckCancelFail(TmpPath: FilePath) -> None:
    Harness, Queue = PrepareTimeout(TmpPath.resolve(), 25)
    Events, RequestPath = BlockCancel(Harness, Queue)
    AssertFirstWait(Events)
    Status = Harness.ReadJob("fixture:timeout")
    Accepted = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("fixture:timeout")))
    assert Status["state"] == Accepted["result"]["outcome"] == "waiting_application"
    assert Accepted["result"]["reason"] == (
        "application reached its deadline and cancellation evidence could not be fully recorded"
    )
    assert "queue_timeout" not in Accepted["result"]["records"]
    assert RequestPath.is_file()
    assert (RequestPath.parent / "cancel.json").is_dir()
    AssertParked(Harness)


# both outcomes need the actual dispatcher supervisor and controller against a private endpoint
def PrepareTimeout(
    RootPath: FilePath, TimeoutSeconds: int
) -> tuple[SessionHost, DispatchHost]:
    Queue = DispatchHost(RootPath)
    Config = JsonCodec.loads(Queue.ConfigFile.read_bytes())
    Config["application"] = "solidworks"
    _ = Queue.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    Harness = SessionHost(RootPath, {"apps": 1}, {"fixture.app": "apps"})
    SetAppRunner(Harness, Queue.ConfigFile, Readback=True)
    Harness.SubmitJobs(
        [
            FixtureJob(
                "fixture:timeout",
                "fixture.app",
                lease_seconds=12,
                timeout_seconds=TimeoutSeconds,
                max_attempts=2,
                resources=["application:missing"],
                options={"source_revision": Config["source_revision"]},
            )
        ]
    )
    return Harness, Queue


# a directory conflict makes cancellation publication fail after the exact request appears
def BlockCancel(
    Harness: SessionHost, Queue: DispatchHost
) -> tuple[list[object], FilePath]:
    Process = Harness.StartRun("--idle-seconds", "2", "--max-seconds", "60")
    try:
        RequestPath = Queue.WaitRequest(Process)
        (RequestPath.parent / "cancel.json").mkdir()
        OutputText, _ = Process.communicate(timeout=65)
        assert Process.returncode == 0, Process.returncode
        return [
            JsonCodec.loads(LineText) for LineText in OutputText.splitlines()
        ], RequestPath
    finally:
        if Process.poll() is None:
            Process.kill()
        _ = Process.communicate(timeout=15)


# a second attempt can mask the exact timeout with an ordinary fence refusal
def AssertFirstWait(Events: list[object]) -> None:
    Terminal = [
        {
            "attempt": Event["attempt"],
            "outcome": Event["outcome"],
            "stop_reason": Event["receipt"]["stop_reason"],
            "exit_status": Event["receipt"]["exit_status"],
        }
        for Event in JsonCodec.loads(JsonCodec.dumps(Events))
        if Event.get("event") == "finished"
    ]
    assert Terminal == [
        {
            "attempt": 1,
            "outcome": "waiting_application",
            "stop_reason": None,
            "exit_status": 0,
        }
    ], Terminal


# a failed cancellation must leave the resource unavailable and retain the job hold
def AssertParked(Harness: SessionHost) -> None:
    assert Harness.StorePath is not None
    Address = (Harness.StorePath / "ledger.sqlite3").as_uri() + "?mode=ro"
    with CloseResource(SqlLayer.connect(Address, uri=True)) as Store:
        Resource = Store.execute(
            "SELECT available, capacity FROM resources WHERE name=?",
            ("application:missing",),
        ).fetchone()
        Parking = Store.execute(
            "SELECT parked FROM jobs WHERE id=?", ("fixture:timeout",)
        ).fetchone()
    assert Resource == (0, 1) and Parking == (1,)


# the retained timeout must bind the specific controller result without creating successful outputs
def AssertTimedLink(Harness: SessionHost, SpoolPath: FilePath) -> None:
    JobInfo = Harness.ReadJob("fixture:timeout")
    Accepted = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("fixture:timeout")))
    RawRequest = (SpoolPath / "phase.request").read_bytes()
    Request = JsonCodec.loads(RawRequest)
    assert JobInfo["state"] == Accepted["result"]["outcome"] == "waiting_application"
    assert "output_artifacts" not in Accepted
    Records = Accepted["result"]["records"]
    assert "queue_timeout" in Records, {
        "record_fields": sorted(Records),
        "fence_refusal": Accepted["result"]["reason"].startswith(
            "installation is fenced"
        ),
        "attempts": JobInfo["attempts"],
    }
    assert Records["queue_timeout"] == {
        "version": 1,
        "installation": Request["installation"],
        "queue_job_id": SpoolPath.name,
        "request_sha256": Hashing.sha256(RawRequest).hexdigest(),
        "nonce": Request["nonce"],
        "client": Request["client"],
        "source_revision": Request["source_revision"],
        "job_id": "fixture:timeout",
        "kind": "fixture.app",
        "resources": ["application:missing"],
        "session": Accepted["receipt"]["session"],
        "generation": JobInfo["generation"],
        "fingerprint": JobInfo["fingerprint"],
        "attempt": JobInfo["attempts"],
    }


# a fresh explicit operator hold must fence a previously accepted timeout even when availability is unchanged
def AssertEpoch(Harness: SessionHost) -> None:
    assert Harness.StorePath is not None
    Original = Harness.ReadJob("fixture:timeout")
    Epoch, Receipt, Output = ReadHold(Harness.StorePath)
    assert Receipt == Original["receipt"] and Output == Original["result"]
    Reaffirm = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:missing",
            "--unavailable",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Reaffirm.returncode == 0, Reaffirm.stderr
    assert ReadHold(Harness.StorePath) == (Epoch + 1, None, None)
    assert Harness.ReadJob("fixture:timeout") == Original


# reopening the store observes the exact persisted hold rather than only the command response
def ReadHold(StorePath: FilePath) -> tuple[int, str | None, str | None]:
    Address = (StorePath / "ledger.sqlite3").as_uri() + "?mode=ro"
    with CloseResource(SqlLayer.connect(Address, uri=True)) as Store:
        HoldInfo: tuple[int, str | None, str | None] | None = Store.execute(
            "SELECT epoch, receipt, result FROM application_holds WHERE resource=?",
            ("application:missing",),
        ).fetchone()
    assert HoldInfo is not None
    return HoldInfo
