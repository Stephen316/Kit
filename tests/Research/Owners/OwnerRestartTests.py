import tempfile as TempFiles
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Owners.InstallGate import InstallGate
from tests.Research.Owners.CheckOwnerTree import CheckOwnerTree
from tests.Research.Owners.CloseGate import CloseGate
from tests.Research.Owners.KillOwner import KillOwner
from tests.Research.Owners.OwnerBarriers import WaitCompleted, WaitRecord
from tests.Research.Owners.OwnerRun import OwnerRun
from tests.Research.Supervisor.Grouping.BatchHost import MakeBatchHost
from tests.Research.Supervisor.Grouping.BatchRecords import BatchJobs


# a replacement owner must reject publication from the old single or grouped claim command
@TestMark.parametrize("Operation", ("claim", "claim-group"))
def CheckOwnerBoot(Operation: str) -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = MakeBatchHost(RootPath)
        GateRoot = InstallGate(Harness, Operation)
        Harness.SubmitJobs(BatchJobs(2, lease_seconds=30, timeout_seconds=60))
        try:
            with OwnerRun(Harness) as First:
                HeldInfo = WaitRecord(GateRoot / "Held.json")
                First.ProcessId = int(str(HeldInfo["supervisor_pid"]))
                OldOwner = WaitRecord(GateRoot / "Owner.json")
                CheckOwnerTree(Harness, HeldInfo, OldOwner)
                KillOwner(First.ProcessId)
                _ = First.Process.communicate(timeout=15)
                with OwnerRun(Harness) as Second:
                    NewOwner = WaitRecord(
                        GateRoot / "Owner.json", str(OldOwner["digest"])
                    )
                    Second.ProcessId = int(str(NewOwner["pid"]))
                    assert NewOwner["pid"] != OldOwner["pid"]
                    _ = (GateRoot / "Release").write_text("release", encoding="ascii")
                    LateInfo = WaitRecord(GateRoot / "Result.json")
                    assert LateInfo["exit_status"] == 5, LateInfo
                    assert "stale supervisor owner" in str(LateInfo["stderr"])
                    assert not FilePath(str(HeldInfo["destination"])).exists()
                    WaitCompleted(Harness, ("batch:00", "batch:01"))
        finally:
            CloseGate(GateRoot)
