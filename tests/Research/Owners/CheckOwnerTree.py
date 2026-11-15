from tests.Research.Owners.ReadParent import ReadParent
from tests.Research.SupervisorClient import SessionHost


# recovery must distinguish the old supervisor command tree from its replacement owner
def CheckOwnerTree(
    Harness: SessionHost, HeldInfo: dict[str, object], OwnerInfo: dict[str, object]
) -> None:
    OwnerPid = int(str(HeldInfo["supervisor_pid"]))
    GatePid = int(str(HeldInfo["gate_pid"]))
    ParentPid = ReadParent(GatePid)
    assert ParentPid == int(str(HeldInfo["parent_pid"]))
    assert OwnerPid == int(str(OwnerInfo["pid"]))
    assert ParentPid is not None
    assert ParentPid == OwnerPid or ReadParent(ParentPid) == OwnerPid
    _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=4)
