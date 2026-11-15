import json as JsonCodec
import re as Regex
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import TypeGuard as TypeCheck

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


# decoded records have interface fields only when the json value is an object
def IsJsonRecord(Value: object) -> TypeCheck[dict[str, object]]:
    return isinstance(Value, dict)


# a typed sequence keeps untrusted decoded entries behind the terminal record check
def IsJsonItems(Value: object) -> TypeCheck[list[object]]:
    return isinstance(Value, list)


# diagnostic reads must stay within calibration metadata bounds even after a partial write
def ReadEvidence(RecordPath: FilePath) -> dict[str, object]:
    try:
        with RecordPath.open("rb") as Source:
            Content = Source.read(1048577)
        if len(Content) > 1048576:
            return {}
        Record: object = JsonCodec.loads(Content)
    except (OSError, ValueError):
        return {}
    return Record if IsJsonRecord(Record) else {}


# report attempt dispositions without releasing job identifiers or worker process identities
def TerminalJobs(TrialPath: FilePath) -> list[dict[str, object]]:
    Report = ReadEvidence(TrialPath / "Trial.json")
    JobsInfo = Report.get("jobs")
    if not IsJsonItems(JobsInfo):
        return []
    return [
        {
            Field: JobInfo.get(Field)
            for Field in ("state", "attempts", "exit_status", "signal", "stop_reason")
        }
        for JobInfo in JobsInfo
        if IsJsonRecord(JobInfo)
        and JobInfo.get("attempts")
        and JobInfo.get("state") != "completed"
    ][:8]


# the terminal event can explain why the controller stopped before a worker result was accepted
def TerminalEvent(Event: object) -> dict[str, object] | None:
    if not IsJsonRecord(Event) or Event.get("event") not in (
        "finished",
        "setup_failed",
        "renew_error",
        "resource_measurement_error",
        "orphan",
    ):
        return None
    if (
        Event["event"] == "finished"
        and Event.get("outcome") == "completed"
        and Event.get("stale") is False
    ):
        return None
    Detail: dict[str, object] = {
        Field: Event[Field] for Field in ("event", "outcome", "stale") if Field in Event
    }
    Receipt = Event.get("receipt")
    if IsJsonRecord(Receipt):
        Detail.update(
            {
                Field: Receipt[Field]
                for Field in ("exit_status", "signal", "stop_reason")
                if Field in Receipt
            }
        )
    Reason = Event.get("error") or Event.get("reason")
    if isinstance(Reason, str):
        Match = Regex.search(
            r"(?:^|: )([A-Za-z][A-Za-z0-9]*(?:Error|Exception|Expired)):", Reason
        )
        if Match:
            Detail["error_type"] = Match[1]
    return Detail


# the final bounded output window preserves failure classifications from the supervisor
def TerminalEvents(TrialPath: FilePath) -> list[dict[str, object]]:
    try:
        LogPath = TrialPath / "stdout.log"
        with LogPath.open("rb") as Source:
            _ = Source.seek(max(0, LogPath.stat().st_size - 32768))
            Content = Source.read(32768)
    except OSError:
        return []
    Events: list[dict[str, object]] = []
    for LineBytes in Content.splitlines():
        try:
            Detail = TerminalEvent(JsonCodec.loads(LineBytes))
        except ValueError:
            continue
        if Detail is not None:
            Events.append(Detail)
    return Events[-8:]


# fixed trial names keep process diagnostics within the private fixture directory
def TrialFailures(OutputPath: FilePath) -> str:
    Details: dict[str, object] = {}
    for Count in (1, 2, 4, 8, 16):
        TrialPath = OutputPath / f"Trial{Count}"
        JobsInfo = TerminalJobs(TrialPath)
        Events = TerminalEvents(TrialPath)
        if JobsInfo or Events:
            Details[TrialPath.name] = {"jobs": JobsInfo, "events": Events}
    return "\nTrial terminal evidence: " + JsonCodec.dumps(Details)[:4096]


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
        + TrialFailures(OutputPath)
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
