import json as JsonCodec
import signal as Signals
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Supervisor.Launch.LaunchHost import KFixturePath


# closing a launch reader must retain the operating system signal needed for diagnosis
def CheckGatePipe() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        ResultInfo = Subprocess.run(
            [
                System.executable,
                str(KFixturePath),
                "pipe-signal",
                "--root",
                str(FilePath(TempPath)),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        assert JsonCodec.loads(ResultInfo.stdout)["signal"] == Signals.SIGPIPE
