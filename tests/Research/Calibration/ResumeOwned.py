import os as OsLayer
import signal as SignalApi
import subprocess as Subprocess
import sys as System

from tests.Research.Calibration.RunCalibration import KRepoRoot


# fixture recovery must verify creation identity before resuming the process it froze
def ResumeOwned(ProcessId: int, Created: str) -> None:
    Program = "import sys;sys.path.insert(0,sys.argv[1]);from Processes import process_start;print(process_start(int(sys.argv[2])))"
    Probe = Subprocess.run(
        [
            System.executable,
            "-c",
            Program,
            str(KRepoRoot / "re/automation"),
            str(ProcessId),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if Probe.returncode == 0 and Probe.stdout.strip() == Created:
        OsLayer.kill(ProcessId, SignalApi.SIGCONT)
