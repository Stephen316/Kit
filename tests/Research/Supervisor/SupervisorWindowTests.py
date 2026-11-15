import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.LearningHost import MakeLearnHost
from tests.Research.SupervisorClient import FixtureJob


# stale memory peaks must expire so the estimator reflects the most recent workload samples
def CheckWindow() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeLearnHost(RootPath)
        Harness.SubmitJobs(
            [
                FixtureJob(f"window:{Index}", "fixture.decode", max_attempts=1)
                for Index in range(55)
            ]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle(MaxSeconds=180)))
        Learned = [Event for Event in Events if Event.get("event") == "memory_estimate"]
        assert len(Learned) == 55
        HistoryFile = RootPath / "SupervisorState" / "memory-history.json"
        History = JsonCodec.loads(HistoryFile.read_text(encoding="utf-8"))
        Samples = History["records"][0]["samples"]
        assert len(Samples) == 50
        assert [Sample["session"] for Sample in Samples] == [
            Event["session"] for Event in Learned[-50:]
        ]
        Peaks = sorted(Sample["peak_memory_bytes"] for Sample in Samples)
        assert Learned[-1]["estimate_bytes"] == (Peaks[47] * 5 + 3) // 4
        assert Learned[-1]["samples"] == 50
