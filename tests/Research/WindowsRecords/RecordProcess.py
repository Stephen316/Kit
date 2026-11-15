import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

KFixture = (
    FilePath(__file__).resolve().parents[3]
    / "re/automation/ApplicationWorkers/WindowsRecordFixture.py"
)


def RunRecord(Operation: str, TargetPath: FilePath) -> dict[str, object]:
    Completed = Subprocess.run(
        [System.executable, str(KFixture), Operation, str(TargetPath)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert Completed.returncode == 0, Completed.stdout + Completed.stderr
    Result: dict[str, object] = JsonCodec.loads(Completed.stdout)
    return Result
