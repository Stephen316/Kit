import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
    ReadSoloMarks,
    ReadTryResult,
)


# group crashes must preserve failure diagnostics while allowing individual members to retry
def CheckBatchCrash() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        Harness.SubmitJobs(BatchJobs(4, options={"crash_group": True}))
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            4,
            1,
            1,
            1,
            1,
        ]
        CheckBatchData(Harness, 4)
        assert len(ReadSoloMarks(RootPath)) == 4
        for Index in range(4):
            JobName = f"batch:{Index:02d}"
            assert Harness.ReadJob(JobName)["attempts"] == 2
            assert (
                ReadTryResult(Harness, JobName)["stderr_tail"]
                == "batch crash diagnostic: member failure\n"
            )


# a bad member artifact must stay isolated without discarding accepted siblings
def CheckBatchFiles() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        JobList = BatchJobs(3)
        JobList[1]["options"] = {"bad_output": True}
        Harness.SubmitJobs(JobList)
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            3,
            1,
        ]
        assert Harness.ReadJob("batch:00")["state"] == "completed"
        assert Harness.ReadJob("batch:02")["state"] == "completed"
        assert Harness.ReadJob("batch:01")["state"] == "failed"
        assert [RowInfo[0] for RowInfo in ReadSoloMarks(RootPath)] == ["batch:01"]
        assert "invalid output artifacts" in str(Harness.ReadJob("batch:01")["reason"])
