import errno as ErrorCodes
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


def CheckBlocked(Outcomes: dict[str, object]) -> None:
    assert set(Outcomes) == {
        "write_crt",
        "write_native",
        "delete",
        "rename",
        "ancestor",
    }, Outcomes
    for Action, Details in Outcomes.items():
        assert isinstance(Details, dict), Outcomes
        if Action == "write_crt":
            assert Details["type"] == "builtins.PermissionError", Outcomes
            assert Details["errno"] == ErrorCodes.EACCES, Outcomes
            assert Details["winerror"] in {None, 5, 32}, Outcomes
            continue
        assert Details["winerror"] in {5, 32}, Outcomes
        if Action != "write_native":
            assert Details["errno"] == ErrorCodes.EACCES, Outcomes
