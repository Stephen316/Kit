import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# owner checks need an independent parent observation to associate a gate with the supervisor
def ReadParent(ProcessId: int) -> int | None:
    Command = (
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(FilePath(__file__).with_suffix(".ps1")),
            str(ProcessId),
        ]
        if System.platform == "win32"
        else ["ps", "-p", str(ProcessId), "-o", "ppid="]
    )
    Result = Subprocess.run(
        Command, capture_output=True, text=True, check=False, timeout=15
    )
    if (
        Result.returncode == (3 if System.platform == "win32" else 1)
        and not Result.stdout.strip()
    ):
        return None
    assert Result.returncode == 0 and Result.stdout.strip().isdigit(), Result.stderr
    return int(Result.stdout.strip())
