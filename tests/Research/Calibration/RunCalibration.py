import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

# the subprocess must use the checked in calibration entry point regardless of the caller directory
KRepoRoot = FilePath(__file__).resolve().parents[3]


# failed sweeps need the stopped trial and completed count in remote process logs
def TrialDetails(ReportPath: FilePath) -> str:
    try:
        Report = JsonCodec.loads(ReportPath.read_text(encoding="utf-8"))
        Details = [
            {
                KeyName: Trial[KeyName]
                for KeyName in (
                    "requested_concurrency",
                    "completed_jobs",
                    "expected_jobs",
                    "wall_seconds",
                    "incomplete_reasons",
                )
            }
            for Trial in Report["trials"]
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    return "\nTrial details: " + JsonCodec.dumps(Details)[:2048]


# calibration checks must verify the actual command exit and durable report together
def RunCalibration(
    ManifestPath: FilePath,
    OutputPath: FilePath,
    ExitCode: int = 0,
    MaxWorkers: int | None = None,
) -> dict[str, object]:
    Process = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Calibration.py"),
            "--manifest",
            str(ManifestPath),
            "--output",
            str(OutputPath),
        ]
        + (["--max-concurrency", str(MaxWorkers)] if MaxWorkers is not None else []),
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    ReportPath = OutputPath / "Calibration.json"
    assert Process.returncode == ExitCode, (
        Process.stderr + Process.stdout + TrialDetails(ReportPath)
    )
    Report: dict[str, object] = JsonCodec.loads(ReportPath.read_text(encoding="utf-8"))
    return Report
