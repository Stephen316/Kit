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


# fixed marker names locate interrupted trials without reading private process records
def TrialMarkers(OutputPath: FilePath) -> str:
    FileNames = (
        "Prepared.json",
        "RegistryContract.json",
        "SupervisorProcess.json",
        "SupervisorInterpreter.json",
        "Cleanup.json",
        "RecoveryReceipt.json",
        "Trial.json",
    )
    Evidence: dict[str, list[str]] = {}
    for Count in (1, 2, 4, 8, 16):
        TrialPath = OutputPath / f"Trial{Count}"
        if TrialPath.is_dir():
            Evidence[TrialPath.name] = [
                FileName for FileName in FileNames if (TrialPath / FileName).is_file()
            ]
    return "\nTrial output markers: " + JsonCodec.dumps(Evidence)


# an abruptly stopped interpreter can return an operating system status without output
def FailureDetails(
    Process: Subprocess.CompletedProcess[str], ExitCode: int, ReportPath: FilePath
) -> str:
    Actual = Process.returncode
    OutputPath = ReportPath.parent
    return (
        f"Calibration {OutputPath.name} exited {Actual} (0x{Actual & 0xFFFFFFFF:08X}) "
        + f"instead of {ExitCode}; {ReportPath.name} present: {ReportPath.is_file()}"
        + TrialMarkers(OutputPath)
        + TrialDetails(ReportPath)
        + f"\nCaptured stderr tail: {Process.stderr[-4096:]!r}"
        + f"\nCaptured stdout tail: {Process.stdout[-2048:]!r}"
    )


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
            "-X",
            "faulthandler",
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
    assert Process.returncode == ExitCode, FailureDetails(Process, ExitCode, ReportPath)
    Report: dict[str, object] = JsonCodec.loads(ReportPath.read_text(encoding="utf-8"))
    return Report
