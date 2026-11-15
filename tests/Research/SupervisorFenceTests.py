import json as JsonCodec
import signal as Signals
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.Supervisor.WaitWorkerEntry import WaitWorkerEntry
from tests.Research.SupervisorClient import (
    FixtureJob,
    IsGoneByTimeout,
    IsProcessGone,
    SessionHost,
)


def ParseEvents(Output: str) -> list[dict[str, object]]:
    Events: list[dict[str, object]] = [
        JsonCodec.loads(LineText) for LineText in Output.splitlines() if LineText
    ]
    return Events


def CheckStaleLease() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        Harness.BindBytes("evidence:hold", b"hold first")
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "stale:hold",
                    "fixture.decode",
                    inputs={"evidence": "evidence:hold"},
                    options={"mode": "hold"},
                )
            ]
        )
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
        try:
            SessionInfo = Harness.WaitSession("stale:hold")
            Changed = TimeClock.monotonic()
            Harness.BindBytes("evidence:hold", b"release")
            Output, ErrorText = Running.communicate(timeout=60)
        finally:
            Running.kill()
            _ = Running.wait()
        assert Running.returncode == 0, ErrorText
        assert TimeClock.monotonic() - Changed < 30
        assert IsProcessGone(int(str(SessionInfo["pid"])))
        Events = ParseEvents(Output)
        Summary = JsonCodec.loads(JsonCodec.dumps(Events[-1]))["summary"]
        assert Summary["stale"] == 1, Events
        assert Summary["finished"] == {"completed": 1}
        Stopped = [
            Event
            for Event in Events
            if Event.get("event") == "finished" and Event.get("outcome") is None
        ]
        assert len(Stopped) == 1
        Receipt = JsonCodec.loads(JsonCodec.dumps(Stopped[0]["receipt"]))
        assert Receipt["stop_reason"] == "stale_lease"
        Released = Harness.ReadJob("stale:hold")
        assert Released["state"] == "completed", Released
        assert Released["generation"] == 2
        assert Released["attempts"] == 1


def WriteFakeReuse(RootPath: FilePath, ProcessId: int) -> None:
    FakePath = RootPath / "SupervisorState" / "sessions" / "fake-reuse"
    FakePath.mkdir(mode=0o700)
    _ = (FakePath / "session.json").write_text(
        JsonCodec.dumps(
            {
                "session_version": 1,
                "session": "fake-reuse",
                "pool": "decode",
                "job_id": "restart:none",
                "attempt": 1,
                "pid": ProcessId,
                "process_start": "linux:1",
            }
        ),
        encoding="utf-8",
    )


def AssertRecovery(
    Events: list[dict[str, object]], Harness: SessionHost, RootPath: FilePath
) -> None:
    Orphans = {
        str(Event["session"]): Event
        for Event in Events
        if Event.get("event") == "orphan"
    }
    assert Orphans["fake-reuse"]["identity_matched"] is False
    assert Orphans["fake-reuse"]["stopped"] is False
    Recovered = [
        Event for SessionName, Event in Orphans.items() if SessionName != "fake-reuse"
    ]
    assert len(Recovered) == 1
    assert Recovered[0]["job_id"] == "restart:first"
    assert Recovered[0]["identity_matched"] is True
    assert Recovered[0]["stopped"] is True
    Summary = JsonCodec.loads(JsonCodec.dumps(Events[-1]))["summary"]
    assert Summary["orphans"] == 2
    Finished = Harness.ReadJob("restart:first")
    assert Finished["state"] == "completed", Finished
    assert Finished["attempts"] == 2
    assert not any((RootPath / "SupervisorState" / "sessions").iterdir())


def CheckRestart() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(RootPath, {"decode": 1}, {"fixture.decode": "decode"})
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "restart:first",
                    "fixture.decode",
                    max_attempts=3,
                    options={"mode": "sleep-first"},
                )
            ]
        )
        First = Harness.StartRun("--idle-seconds", "30", "--max-seconds", "90")
        Bystander = Subprocess.Popen(
            [System.executable, "-c", "import time; time.sleep(120)"],
            start_new_session=True,
        )
        try:
            SessionInfo = Harness.WaitSession("restart:first")
            OrphanId = int(str(SessionInfo["pid"]))
            WaitWorkerEntry(RootPath, str(SessionInfo["session"]), OrphanId)
            First.send_signal(Signals.SIGKILL)
            _ = First.communicate(timeout=30)
            assert not IsProcessGone(OrphanId)
            WriteFakeReuse(RootPath, Bystander.pid)
            Events = ParseEvents(
                Harness.RunCli(
                    "run", "--idle-seconds", "3", "--max-seconds", "60", Timeout=120
                )
            )
            assert IsGoneByTimeout(OrphanId)
            assert Bystander.poll() is None
        finally:
            First.kill()
            _ = First.wait()
            Bystander.kill()
            _ = Bystander.wait()
        AssertRecovery(Events, Harness, RootPath)


def CheckAdapter() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = SessionHost(
            RootPath,
            {"decode": 1},
            {"fixture.decode": "decode"},
            {
                "module": str(FilePath(__file__).with_name("MiniController.py")),
                "class": "MiniController",
                "options": {"root": str(RootPath / "Mini")},
            },
        )
        Harness.BindBytes("evidence:mini", b"mini evidence")
        Harness.BindBytes("evidence:hold", b"hold mini")
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "mini:complete",
                    "fixture.decode",
                    inputs={"evidence": "evidence:mini"},
                    options={"mode": "complete"},
                ),
                FixtureJob("mini:crash", "fixture.decode", options={"mode": "crash"}),
                FixtureJob(
                    "mini:hold",
                    "fixture.decode",
                    inputs={"evidence": "evidence:hold"},
                    options={"mode": "hold"},
                ),
            ]
        )
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "90")
        try:
            _ = Harness.WaitSession("mini:hold", Timeout=60)
            _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=4)
            Harness.BindBytes("evidence:hold", b"release")
            Output, ErrorText = Running.communicate(timeout=90)
        finally:
            Running.kill()
            _ = Running.wait()
        assert Running.returncode == 0, ErrorText
        Summary = JsonCodec.loads(JsonCodec.dumps(ParseEvents(Output)[-1]))["summary"]
        assert Summary["stale"] == 1
        assert Summary["finished"] == {"completed": 2, "retry": 2}
        AssertAdapter(Harness)


def AssertAdapter(Harness: SessionHost) -> None:
    Complete = Harness.ReadJob("mini:complete")
    assert Complete["state"] == "completed"
    Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("mini:complete")))
    assert Stored["result"]["records"]["tokenless"] is True
    assert len(Stored["result"]["records"]["inputs"]) == 1
    Crash = Harness.ReadJob("mini:crash")
    assert Crash["state"] == "failed"
    assert Crash["attempts"] == 2
    Released = Harness.ReadJob("mini:hold")
    assert Released["state"] == "completed", Released
    assert Released["generation"] == 2
