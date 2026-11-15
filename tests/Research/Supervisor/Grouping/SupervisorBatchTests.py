import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
)


def CheckBatchCap() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        Harness.SubmitJobs(BatchJobs(25, options={"hold_seconds": 4}))
        Events = Harness.RunIdle(MaxSeconds=60)
        Started = BatchEvents(Events, "started")
        assert [Record["group_size"] for Record in Started] == [20, 5]
        CheckBatchData(Harness, 25)
        for GroupSize in (5, 20):
            HistoryFile = (
                RootPath
                / "SupervisorState"
                / f"group-memory-history-{GroupSize:02d}.json"
            )
            History = JsonCodec.loads(HistoryFile.read_text(encoding="utf-8"))
            assert len(History["records"]) == 1
            assert len(History["records"][0]["samples"]) == 1
        assert not (RootPath / "SupervisorState" / "memory-history.json").exists()


def CheckBatchKeys() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeBatchHost(FilePath(TempPath))
        JobList = BatchJobs(7)
        JobList[2]["tool_version"], JobList[3]["tool_version"] = "tool@2", "tool@2"
        JobList[4]["rule_version"], JobList[5]["rule_version"] = "rule@2", "rule@2"
        Harness.BindBytes("large", b"x" * 1048576)
        JobList[6]["inputs"] = {"source": "large"}
        Harness.SubmitJobs(JobList)
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            2,
            2,
            2,
            1,
        ]
        CheckBatchData(Harness, 7)


def CheckBatchBytes() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        Harness = MakeBatchHost(FilePath(TempPath))
        Harness.BindBytes("source", b"x" * 524288)
        Harness.SubmitJobs(BatchJobs(2))
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            1,
            1,
        ]
        CheckBatchData(Harness, 2)
