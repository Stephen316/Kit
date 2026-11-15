import json as JsonCodec
import os as OsLayer
import signal as SignalApi
import subprocess as Subprocess
import sys as System

from tests.Research.Calibration.RunCalibration import KRepoRoot

KLeaderCode = """
import subprocess, sys
child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(120)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(child.pid, flush=True)
sys.stdin.read()
"""
KProbeCode = """
import json, sys
sys.path.insert(0, sys.argv[1])
from Processes import group_running, process_start
print(json.dumps({'created': process_start(int(sys.argv[2])), 'running': group_running(int(sys.argv[2]))}))
"""


def ProbeProcess(ProcessId: int) -> dict[str, object]:
    ResultInfo = Subprocess.run(
        [
            System.executable,
            "-c",
            KProbeCode,
            str(KRepoRoot / "re/automation"),
            str(ProcessId),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    Record: dict[str, object] = JsonCodec.loads(ResultInfo.stdout)
    return Record


def StopChild(ProcessId: int, Created: object) -> None:
    if Created is not None and ProbeProcess(ProcessId)["created"] == Created:
        OsLayer.kill(ProcessId, SignalApi.SIGKILL)
