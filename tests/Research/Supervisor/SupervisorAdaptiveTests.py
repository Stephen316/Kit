import json as JsonCodec
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.Supervisor.CheckAdaptive import CheckAdaptive
from tests.Research.SupervisorClient import FixtureJob


def CheckRealMinute() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeAdaptive(RootPath)
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "adaptive:hold",
                    "fixture.decode",
                    max_attempts=1,
                    lease_seconds=30,
                    timeout_seconds=90,
                    options={"hold_seconds": 65},
                ),
                FixtureJob(
                    "adaptive:next",
                    "fixture.decode",
                    max_attempts=1,
                    lease_seconds=30,
                    timeout_seconds=90,
                ),
            ]
        )
        StartedAt = TimeClock.monotonic()
        Events = JsonCodec.loads(
            JsonCodec.dumps(Harness.RunIdle(IdleSeconds=2, MaxSeconds=150))
        )
        assert TimeClock.monotonic() - StartedAt >= 60
        Started = [Event for Event in Events if Event.get("event") == "started"]
        assert len(Started) == 2
        assert Started[1]["at"] - Started[0]["at"] >= 60
        assert Harness.ReadJob("adaptive:hold")["state"] == "completed"
        assert Harness.ReadJob("adaptive:next")["state"] == "completed"
        CheckAdaptive(Events)
