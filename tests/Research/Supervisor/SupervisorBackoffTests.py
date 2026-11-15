import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.AdaptiveHost import MakeAdaptive
from tests.Research.SupervisorClient import FixtureJob


# repeated deadline stops must reduce pool concurrency without obscuring the job failure reason
def CheckDeadlines() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeAdaptive(FilePath(TempPath), PoolLimit=8)
        Harness.SubmitJobs(
            [
                FixtureJob(
                    f"adaptive:deadline{Index}",
                    "fixture.decode",
                    max_attempts=1,
                    timeout_seconds=6,
                    options={"mode": "deadline"},
                )
                for Index in range(2)
            ]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(IdleSeconds=2)))
        Backoffs = [
            Event for Event in Events if Event.get("event") == "adaptive_backoff"
        ]
        assert len(Backoffs) == 1
        assert Backoffs[0]["adaptive_reason"] == "deadline_pair"
        assert Backoffs[0]["deadline_count"] == 2
        assert Backoffs[0]["deadline_window_seconds"] == 600
        assert Backoffs[0]["target_limit"] == max(1, Backoffs[0]["before_limit"] // 2)
        for Index in range(2):
            Stopped = Harness.ReadJob(f"adaptive:deadline{Index}")
            assert Stopped["state"] == "failed"
            assert Stopped["reason"] == "session stopped: deadline"
        print(
            JsonCodec.dumps(
                {
                    "adaptive_deadline_backoff_verified": True,
                    "adaptive_numeric_reduction_verified": Backoffs[0]["target_limit"]
                    < Backoffs[0]["before_limit"],
                    "backoff": Backoffs[0],
                }
            )
        )
