import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


class JobClient:
    def __init__(self, RootPath: FilePath, Maximum: int = 2) -> None:
        super().__init__()
        self.Command = [
            System.executable,
            str(
                FilePath(__file__).resolve().parents[2] / "re/automation/Controller.py"
            ),
            "--store",
            str(RootPath / "State"),
        ]
        _ = self.RunCli("init", "--max-running", str(Maximum))

    def RunCli(self, *ArgItems: str, ExitCode: int = 0) -> str:
        ResultInfo = Subprocess.run(
            self.Command + list(ArgItems),
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert ResultInfo.returncode == ExitCode, ResultInfo.stderr
        return ResultInfo.stdout
