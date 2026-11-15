import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[3]


def RunCalibration(
    ManifestPath: FilePath, OutputPath: FilePath, ExitCode: int = 0
) -> dict[str, object]:
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    assert Process.returncode == ExitCode, Process.stderr + Process.stdout
    Report: dict[str, object] = JsonCodec.loads(
        (OutputPath / "Calibration.json").read_text(encoding="utf-8")
    )
    return Report
