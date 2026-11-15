import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.LearningHost import MakeLearnHost
from tests.Research.SupervisorClient import FixtureJob


def CheckLearning() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeLearnHost(RootPath)
        Harness.SubmitJobs(
            [
                FixtureJob(f"learn:{Index}", "fixture.decode", max_attempts=1)
                for Index in range(5)
            ]
        )
        Events = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle()))
        Learned = [Event for Event in Events if Event.get("event") == "memory_estimate"]
        assert len(Learned) == 5
        assert [Event["source"] for Event in Learned[:4]] == ["initial"] * 4
        HistoryFile = RootPath / "SupervisorState" / "memory-history.json"
        History = JsonCodec.loads(HistoryFile.read_text(encoding="utf-8"))
        Peaks = [
            Sample["peak_memory_bytes"] for Sample in History["records"][0]["samples"]
        ]
        assert Learned[-1]["source"] == "p95+25%"
        assert Learned[-1]["estimate_bytes"] == (max(Peaks) * 5 + 3) // 4
        Harness.SubmitJobs(
            [
                FixtureJob(
                    "learn:version",
                    "fixture.decode",
                    max_attempts=1,
                    tool_version="tool@2",
                )
            ]
        )
        Reopened = JsonCodec.loads(JsonCodec.dumps(Harness.RunIdle()))
        NewVersion = [
            Event for Event in Reopened if Event.get("event") == "memory_estimate"
        ]
        assert len(NewVersion) == 1
        assert NewVersion[0]["tool_version"] == "tool@2"
        assert NewVersion[0]["source"] == "initial"
        assert NewVersion[0]["estimate_bytes"] == 128 * 1048576
        History = JsonCodec.loads(HistoryFile.read_text(encoding="utf-8"))
        assert {
            Entry["tool_version"]: len(Entry["samples"]) for Entry in History["records"]
        } == {"tool@1": 5, "tool@2": 1}
