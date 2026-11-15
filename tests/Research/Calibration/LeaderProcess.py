import json as JsonCodec
import os as OsLayer
import signal as SignalApi
import subprocess as Subprocess
import sys as System

from tests.Research.Calibration.RunCalibration import KRepoRoot

# the cleanup fixture needs a leader and surviving child whose lifetimes can be controlled separately
KLeaderCode = """
import subprocess, sys
child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(120)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(child.pid, flush=True)
sys.stdin.read()
"""

# the caller needs production identity and liveness evidence without accessing foreign process state directly
KProbeCode = """
import json, sys
sys.path.insert(0, sys.argv[1])
from Processes import group_running, process_start
print(json.dumps({'created': process_start(int(sys.argv[2])), 'running': group_running(int(sys.argv[2]))}))
"""


# a separate probe provides the same process identity evidence that cleanup relies on
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


# fixture teardown must avoid signaling an unrelated process if the original identifier was recycled
def StopChild(ProcessId: int, Created: object) -> None:
    if Created is not None and ProbeProcess(ProcessId)["created"] == Created:
        OsLayer.kill(ProcessId, SignalApi.SIGKILL)
