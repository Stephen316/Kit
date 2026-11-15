import hashlib as Hashing
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionCommand, SessionHost


# real workers must produce distinct durable outcomes for success and each supported failure case
def CheckOutcomes() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(
            RootPath,
            {"decode": 2, "other": 1},
            {"fixture.decode": "decode", "fixture.other": "other"},
        )
        Harness.BindBytes("evidence:one", b"evidence bytes")
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "outcome:complete",
                    "fixture.decode",
                    inputs={"evidence": "evidence:one"},
                    options={"mode": "complete", "records": {"count": 7}},
                ),
                FixtureJob(
                    "outcome:rejected",
                    "fixture.other",
                    options={"mode": "complete", "outcome": "rejected"},
                ),
                FixtureJob(
                    "outcome:invalid",
                    "fixture.decode",
                    max_attempts=1,
                    options={"mode": "invalid"},
                ),
                FixtureJob(
                    "outcome:schema",
                    "fixture.decode",
                    max_attempts=1,
                    options={"mode": "complete", "records": {"count": "many"}},
                ),
                FixtureJob(
                    "outcome:crash", "fixture.decode", options={"mode": "crash"}
                ),
                FixtureJob("outcome:unpooled", "fixture.unpooled"),
            ]
        )
        Events = Harness.RunIdle(IdleSeconds=4)
        Summary = JsonCodec.loads(JsonCodec.dumps(Events[-1]))["summary"]
        assert Summary["started"] == 6, Events
        assert Summary["finished"] == {"completed": 1, "rejected": 1, "retry": 4}
        AssertReceipt(Harness)
        AssertFailures(Harness)
        StatePath = RootPath / "SupervisorState"
        assert not any((StatePath / "sessions").iterdir())
        assert not any((StatePath / "claims").iterdir())


# a completion only counts when the controller retains the worker result and its evidence
def AssertReceipt(Harness: SessionHost) -> None:
    Complete = Harness.ReadJob("outcome:complete")
    assert Complete["state"] == "completed", Complete
    Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("outcome:complete")))
    assert Stored["result"]["records"] == {
        "count": 7,
        "inputs": [Hashing.sha256(b"evidence bytes").hexdigest()],
        "tokenless": True,
    }
    assert Stored["receipt"]["exit_status"] == 0
    assert Stored["receipt"]["signal"] is None
    assert Stored["receipt"]["peak_memory_bytes"] > 0


# rejected input and invalid output must remain distinguishable for downstream recovery
def AssertFailures(Harness: SessionHost) -> None:
    assert Harness.ReadJob("outcome:rejected")["state"] == "rejected"
    Invalid = Harness.ReadJob("outcome:invalid")
    assert Invalid["state"] == "failed"
    assert str(Invalid["reason"]).startswith("invalid result:")
    Schema = Harness.ReadJob("outcome:schema")
    assert Schema["state"] == "failed"
    assert "$.records.count" in str(Schema["reason"])
    Crash = Harness.ReadJob("outcome:crash")
    assert Crash["state"] == "failed"
    assert Crash["attempts"] == 2
    assert Crash["reason"] == "runner exited with status 3"
    CrashResult = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("outcome:crash")))
    assert "fixture failure" in CrashResult["stderr_tail"]
    Unpooled = Harness.ReadJob("outcome:unpooled")
    assert Unpooled["state"] == "queued"
    assert Unpooled["attempts"] == 0


# deadline handling must reclaim worker capacity after a session runs past its allowance
def CheckDeadline() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "deadline:term",
                    "fixture.decode",
                    max_attempts=1,
                    timeout_seconds=6,
                    options={"mode": "ignore-term"},
                )
            ]
        )
        _ = Harness.RunIdle(IdleSeconds=2)
        Stopped = Harness.ReadJob("deadline:term")
        assert Stopped["state"] == "failed", Stopped
        assert Stopped["reason"] == "session stopped: deadline"
        Receipt = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("deadline:term")))[
            "receipt"
        ]
        assert Receipt["stop_reason"] == "deadline"
        assert Receipt["signal"] == 9
        assert 3 <= Receipt["duration_seconds"] < 6


# live status must retain the active decision only for the configuration the supervisor actually loaded
def ReadLiveCap(Harness: SessionHost) -> tuple[int, int, int]:
    PoolInfo = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
    assert [SessionRow["job_id"] for SessionRow in PoolInfo["running"]] == ["busy:hold"]
    assert PoolInfo["max_sessions"] == 1 and PoolInfo["paused"] is None
    Decision = PoolInfo["capacity"]["decision"]
    assert Decision["active_limit"] == Decision["calculated_capacity"] == 1
    assert "configured" in Decision["limiting_factors"]
    Estimates = Decision["memory_estimate_bytes_by_kind"]
    assert Estimates == {"fixture.decode": 1024 * 1048576}
    ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    ConfigInfo["reserved_cpus"] = 1
    Different = Harness.RootPath / "DifferentConfig.json"
    _ = Different.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    Mismatched = JsonCodec.loads(SessionCommand(Different).RunCli("status"))
    assert Mismatched["pools"]["decode"]["capacity"] == {
        "state": "unavailable",
        "decision": None,
    }
    return (
        Decision["active_limit"],
        Decision["calculated_capacity"],
        max(Estimates.values()),
    )


# archived admission and shutdown evidence must validate the numbers seen in a previously live view
def VerifyCapExit(
    Harness: SessionHost, Output: str, LiveValues: tuple[int, int, int]
) -> None:
    Events = [JsonCodec.loads(LineText) for LineText in Output.splitlines()]
    Admission = next(Event for Event in Events if Event["event"] == "admission")
    assert LiveValues == (
        Admission["active_limit"],
        Admission["calculated_capacity"],
        Admission["estimated_memory_bytes"],
    )
    Retired = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
    assert Retired["capacity"] == {"state": "unavailable", "decision": None}


# pausing dispatch must keep existing ownership and prevent another supervisor from taking the same state
def CheckPauseLock() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        Harness.SubmitJobs(
            [FixtureJob("busy:hold", "fixture.decode", options={"mode": "sleep-first"})]
        )
        First = Harness.StartRun("--idle-seconds", "8", "--max-seconds", "60")
        try:
            _ = Harness.WaitSession("busy:hold")
            _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=4)
            LiveValues = ReadLiveCap(Harness)
            _ = Harness.RunCli("pause", "decode", "--reason", "operator hold")
            Harness.WaitReason("busy:hold", "session stopped: pool_paused")
            Paused = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
            assert Paused["paused"]["reason"] == "operator hold"
            assert Paused["capacity"] == {"state": "paused", "decision": None}
            assert Harness.ReadJob("busy:hold")["attempts"] == 1
            _ = Harness.RunCli("resume", "decode")
            Output, _ = First.communicate(timeout=60)
        finally:
            First.kill()
            _ = First.wait()
        assert First.returncode == 0
        VerifyCapExit(Harness, Output, LiveValues)
        Resumed = Harness.ReadJob("busy:hold")
        assert Resumed["state"] == "completed", Resumed
        assert Resumed["attempts"] == 2
