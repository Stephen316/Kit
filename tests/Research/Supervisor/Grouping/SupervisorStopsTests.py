import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchProcess import SetGroupFloor
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
)


def CheckBatchMem() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        SetGroupFloor(RootPath, 64)
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["adaptive_limits"] = True
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            BatchJobs(3, options={"hold_seconds": 30, "memory_mib": 120})
        )
        Events = Harness.RunIdle()
        Backoffs = BatchEvents(Events, "adaptive_backoff")
        assert len(Backoffs) == 1
        assert Backoffs[0]["adaptive_reason"] == "memory_limit"
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            3,
            1,
            1,
            1,
        ]
        CheckBatchData(Harness, 3)
        assert not list(
            (RootPath / "SupervisorState").glob("group-memory-history-*.json")
        )


def CheckBatchTime() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["adaptive_limits"] = True
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            BatchJobs(3, timeout_seconds=8, options={"hold_seconds": 30})
        )
        Events = Harness.RunIdle()
        assert not BatchEvents(Events, "adaptive_backoff")
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            3,
            1,
            1,
            1,
        ]
        CheckBatchData(Harness, 3)
