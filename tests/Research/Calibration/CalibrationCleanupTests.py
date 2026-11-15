import subprocess as Subprocess
import sys as System

from tests.Research.Calibration.LeaderProcess import (
    KLeaderCode,
    ProbeProcess,
    StopChild,
)
from tests.Research.Calibration.RunCalibration import KRepoRoot
from tests.Research.SupervisorClient import IsGoneByTimeout

# cleanup refusal must be observable across a process boundary with live descendants
KRetireCode = """
import sys
sys.path.insert(0, sys.argv[1])
from CalibrationProcesses import stop_groups
stop_groups({int(sys.argv[2]): sys.argv[3]})
"""


# a vanished group leader cannot authorize killing descendants whose ownership is no longer provable
def CheckLostLeader() -> None:
    Leader = Subprocess.Popen(
        [System.executable, "-c", KLeaderCode],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    assert Leader.stdout is not None and Leader.stdin is not None
    ChildId = int(Leader.stdout.readline())
    Created = ProbeProcess(ChildId)["created"]
    try:
        LeaderStart = ProbeProcess(Leader.pid)["created"]
        assert isinstance(LeaderStart, str) and isinstance(Created, str)
        Leader.stdin.close()
        assert Leader.wait(timeout=15) == 0
        assert ProbeProcess(Leader.pid) == {"created": None, "running": True}
        VerifyRefusal(Leader.pid, LeaderStart)
        assert ProbeProcess(ChildId)["created"] == Created
        assert ProbeProcess(Leader.pid)["running"] is True
    finally:
        StopChild(ChildId, Created)
        if Leader.poll() is None:
            Leader.terminate()
            _ = Leader.wait(timeout=15)
    assert IsGoneByTimeout(ChildId)


# an independently invoked cleanup probe must report refusal without stopping the residual group
def VerifyRefusal(ProcessId: int, Created: str) -> None:
    ResultInfo = Subprocess.run(
        [
            System.executable,
            "-c",
            KRetireCode,
            str(KRepoRoot / "re/automation"),
            str(ProcessId),
            Created,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert ResultInfo.returncode != 0
    assert "an owned calibration worker group could not be stopped" in ResultInfo.stderr
