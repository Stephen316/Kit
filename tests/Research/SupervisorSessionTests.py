import hashlib as Hashing
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import FixtureJob, SessionHost


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
            StatusInfo = JsonCodec.loads(Harness.RunCli("status"))
            Running = StatusInfo["pools"]["decode"]["running"]
            assert [SessionRow["job_id"] for SessionRow in Running] == ["busy:hold"]
            _ = Harness.RunCli("pause", "decode", "--reason", "operator hold")
            Harness.WaitReason("busy:hold", "session stopped: pool_paused")
            Paused = JsonCodec.loads(Harness.RunCli("status"))["pools"]["decode"]
            assert Paused["paused"]["reason"] == "operator hold"
            assert Harness.ReadJob("busy:hold")["attempts"] == 1
            _ = Harness.RunCli("resume", "decode")
            _ = First.communicate(timeout=60)
        finally:
            First.kill()
            _ = First.wait()
        assert First.returncode == 0
        Resumed = Harness.ReadJob("busy:hold")
        assert Resumed["state"] == "completed", Resumed
        assert Resumed["attempts"] == 2
