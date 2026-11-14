from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as KPythonPath


def CliProcess(Directory: FilePath, *Arguments: str) -> CompletedProcess[str]:
    return RunProcess(
        (KPythonPath, "-m", "convert", *Arguments),
        cwd=Directory,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
