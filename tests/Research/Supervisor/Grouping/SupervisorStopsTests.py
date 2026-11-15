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


# a grouped memory stop must protect the pool without teaching the estimator an invalid sample
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


# a process stop whose members are all fenced must not influence later pool decisions
def CheckStaleGroup() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        SetGroupFloor(RootPath, 64)
        _ = (RootPath / "Replacement.bin").write_bytes(b"replacement input")
        AdapterFile = RootPath / "GroupRebindAdapter.py"
        _ = AdapterFile.write_text(
            """from Adapters import A03Adapter


# the controller must fence the group after the physical process has already stopped
class GroupRebindAdapter(A03Adapter):

    # rebinding at the finish boundary makes supersession independent of process timing
    def FinishGroup(self, path, result):
        self.BindInput("source", self.store.parent / "Replacement.bin")
        return super().FinishGroup(path, result)
""",
            encoding="utf-8",
        )
        ConfigInfo = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
        ConfigInfo["adaptive_limits"] = True
        ConfigInfo["controller"] = {
            "module": str(AdapterFile),
            "class": "GroupRebindAdapter",
            "options": {"store": str(Harness.StorePath)},
        }
        _ = Harness.ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
        Harness.SubmitJobs(
            BatchJobs(3, options={"hold_seconds": 30, "memory_mib": 120})
        )
        Events = Harness.RunIdle()
        FirstGroup = BatchEvents(Events, "started")[0]
        assert FirstGroup["group_size"] == 3
        FirstFinishes = [
            Record
            for Record in BatchEvents(Events, "finished")
            if Record["session"] == FirstGroup["session"]
        ]
        assert len(FirstFinishes) == 3
        assert all(
            Record["stale"] is True
            and Record["outcome"] is None
            and Record["reason"] == "session stopped: memory_limit"
            for Record in FirstFinishes
        )
        assert all(
            Record["session"] != FirstGroup["session"]
            for Record in BatchEvents(Events, "adaptive_backoff")
        )
        CheckBatchData(Harness, 3)
        assert all(
            Harness.ReadJob(f"batch:{Index:02d}")["generation"] == 2
            for Index in range(3)
        )


# one grouped deadline must recover its members without counting as multiple pool deadline failures
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
