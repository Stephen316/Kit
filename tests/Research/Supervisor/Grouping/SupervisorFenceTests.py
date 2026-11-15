import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchProcess import WaitBatchFlag
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
)


def CheckBatchFence() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        FlagFile = RootPath / "Started.pid"
        Harness.BindBytes("other", b"independent source")
        JobList = BatchJobs(
            3, options={"hold_seconds": 15, "started_file": str(FlagFile)}
        )
        JobList[1]["inputs"] = {"source": "other"}
        Harness.SubmitJobs(JobList)
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
        try:
            WaitBatchFlag(FlagFile, Running)
            Harness.BindBytes("other", b"new source invalidates one lease")
            OutputText, ErrorText = Running.communicate(timeout=90)
            assert Running.returncode == 0, ErrorText
            Events = [JsonCodec.loads(LineText) for LineText in OutputText.splitlines()]
            assert BatchEvents(Events, "started")[0]["group_size"] == 3
            assert all(
                Record["group_size"] == 1
                for Record in BatchEvents(Events, "started")[1:]
            )
            CheckBatchData(Harness, 3)
            assert Harness.ReadJob("batch:01")["generation"] == 2
        finally:
            if Running.poll() is None:
                Running.kill()
            _ = Running.wait()
