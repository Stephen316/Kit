import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchProcess import SetBatchSlots, SetGroupFloor
from tests.Research.Supervisor.Grouping.BatchRecords import (
    BatchEvents,
    BatchJobs,
    CheckBatchData,
)


# a limit shared with other work must constrain the number of grouped leases
def CheckBatchSlots() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        SetBatchSlots(RootPath, 3)
        Harness.SubmitJobs(BatchJobs(5, resources=["fixture:slots"]))
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            3,
            2,
        ]
        CheckBatchData(Harness, 5)


# insufficient headroom for the group should leave eligible individual jobs runnable
def CheckBatchFloor() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        SetGroupFloor(RootPath, 1048576)
        Harness.SubmitJobs(BatchJobs(2))
        Events = Harness.RunIdle()
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            1,
            1,
        ]
        CheckBatchData(Harness, 2)
