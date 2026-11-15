import hashlib as HashCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchRecords import BatchEvents, BatchJobs


# aggregate artifact limits must protect the store even when each member appears individually admissible
def CheckBatchTotal() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Harness = MakeBatchHost(RootPath)
        Harness.SubmitJobs(BatchJobs(2, options={"output_size_mib": 200}))
        Events = Harness.RunIdle()
        Finished = BatchEvents(Events, "finished")
        assert all(
            Record["reason"] == "group output declarations exceed 256 MiB in aggregate"
            for Record in Finished[:2]
        )
        assert [Record["group_size"] for Record in BatchEvents(Events, "started")] == [
            2,
            1,
            1,
        ]
        assert Harness.StorePath is not None
        for Index in range(2):
            JobName = f"batch:{Index:02d}"
            assert Harness.ReadJob(JobName)["state"] == "failed"
            HashValue = HashCodec.sha256(JobName.encode("ascii")).hexdigest()
            assert not (
                Harness.StorePath / "objects" / HashValue[:2] / HashValue
            ).exists()
