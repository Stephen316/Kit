import os as OsLayer
import signal as Signals
import subprocess as Subprocess
import sys as System


# abrupt owner loss must reach the real subprocess across supported host platforms
def KillOwner(ProcessId: int, Required: bool = True) -> None:
    if System.platform == "win32":
        Result = Subprocess.run(
            ["taskkill.exe", "/PID", str(ProcessId), "/F"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if Required:
            assert Result.returncode == 0, Result.stderr
        return
    try:
        OsLayer.kill(ProcessId, Signals.SIGKILL)
    except ProcessLookupError:
        if Required:
            raise
