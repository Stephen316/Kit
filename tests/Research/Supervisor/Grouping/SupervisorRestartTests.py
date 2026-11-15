import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchProcess import WaitBatchFlag
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
    ReadSoloMarks,
)
from tests.Research.SupervisorClient import IsGoneByTimeout


def CheckBatchBoot() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        FlagFile = RootPath / "Started.pid"
        Harness.SubmitJobs(
            BatchJobs(4, options={"hold_seconds": 30, "started_file": str(FlagFile)})
        )
        Running = Harness.StartRun("--idle-seconds", "3", "--max-seconds", "60")
        try:
            WaitBatchFlag(FlagFile, Running)
            ProcessId = int(FlagFile.read_text(encoding="ascii"))
            Running.kill()
            _ = Running.communicate(timeout=30)
            Events = Harness.RunIdle()
            assert IsGoneByTimeout(ProcessId)
            assert [
                Record["group_size"] for Record in BatchEvents(Events, "started")
            ] == [1, 1, 1, 1]
            assert len(ReadSoloMarks(RootPath)) == 4
            CheckBatchData(Harness, 4)
        finally:
            if Running.poll() is None:
                Running.kill()
            _ = Running.wait()
