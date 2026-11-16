import json as JsonCodec
import subprocess as Subprocess
import sys as System
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionColdWatch import AwaitStatus, RunOwner
from tests.Research.SupervisorClient import SessionHost


# real launch services and the pinned bootstrap must establish a new process without a retry claim
def VerifyLaunch(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Flags: list[str],
    PhaseName: str,
    Verified: dict[str, object],
) -> None:
    (Dispatch.RootPath / "stop").unlink()
    (Dispatch.RootPath / "ready.json").unlink()
    ArchiveHash = Verified["archive_manifest_sha256"]
    LaunchPath = Dispatch.Endpoint / f"archived-replacement-launch-{ArchiveHash}.json"
    PeerPath = Dispatch.Endpoint / f"archived-replacement-peer-{ArchiveHash}.json"
    StartupPath = Dispatch.Endpoint / f"archived-replacement-startup-{ArchiveHash}.json"
    Enabled = [*Flags, "--launch-archived-replacement"]
    with RunOwner(Dispatch, Enabled, "LaunchOwner") as LogPath:
        Report = AwaitStatus(
            LogPath,
            "phase_a_probe_archived",
            Replacement="startup_verified_control_pending",
            WaitSeconds=65,
        )
        AssertNewPeer(Dispatch, LaunchPath, PeerPath, StartupPath, Report)
    LoseLaunchReply(Dispatch, Enabled, LaunchPath, PeerPath, StartupPath)
    LoseLaunchSeal(Dispatch, Enabled, LaunchPath)
    VerifyControl(Dispatch, Enabled, str(ArchiveHash), PeerPath)
    RefuseManual(Dispatch, Harness, str(ArchiveHash))
    First = Harness.ReadJob(PhaseName)
    assert First["state"] == "waiting_application" and First["attempts"] == 1
    assert Harness.ReadJob("fixture:cold-rival")["attempts"] == 0


# old manual admission must defer to the sealed automatic control owner
def RefuseManual(
    Dispatch: DispatchHost, Harness: SessionHost, ArchiveHash: str
) -> None:
    Command = KRepoRoot / "re/automation/ApplicationWorkers/RetryFusionProbe.py"
    Outcome = Subprocess.run(
        [
            System.executable,
            "-B",
            str(Command),
            "--config",
            str(Harness.ConfigFile),
            "--queue-receipt",
            str(Dispatch.RootPath / "ColdPair.json"),
            "--archive-manifest-sha256",
            ArchiveHash,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert Outcome.returncode == 1, Outcome.stdout + Outcome.stderr
    assert "reserved for the archived control owner" in Outcome.stderr


# the replacement process runs the pinned native control path before any second claim
def VerifyControl(
    Dispatch: DispatchHost, Enabled: list[str], ArchiveHash: str, PeerPath: FilePath
) -> None:
    (Dispatch.RootPath / "exercise-archive-control").touch()
    Flags = [*Enabled, "--measure-archived-replacement"]
    with RunOwner(Dispatch, Flags, "ControlOwner") as LogPath:
        Report = AwaitStatus(
            LogPath,
            "phase_a_probe_archived",
            Replacement="control_verified_admission_pending",
            WaitSeconds=45,
        )
    Request = Dispatch.Endpoint / f"archived-control-request-{ArchiveHash}.json"
    Attempt = Dispatch.Endpoint / f"archived-control-attempt-{ArchiveHash}.json"
    Result = Dispatch.Endpoint / f"archived-control-result-{ArchiveHash}.json"
    ReportHash = Report["archive_replacement_control_sha256"]
    assert Report["resource_rearmed"] is False
    assert ReportHash == HashBytes(Result.read_bytes()).hexdigest()
    Reply = JsonCodec.loads(Result.read_bytes())
    ReplacementPeer = JsonCodec.loads(PeerPath.read_bytes())["peer"]
    assert Reply["peer"]["pid"] == ReplacementPeer["pid"]
    assert Reply["request_sha256"] == HashBytes(Request.read_bytes()).hexdigest()
    assert Reply["attempt_sha256"] == HashBytes(Attempt.read_bytes()).hexdigest()
    Reading = Reply["proof"]["readings"]["healthy_control"]
    assert Reading["after_recompute"]["volume_mm3"] == 30_000
    assert Reading["compute_all_return"] is True
    assert Reply["proof"]["documents_after"] == 0
    assert not (Dispatch.RootPath / "document-open").exists()
    assert not (Dispatch.Endpoint / "grant.json").exists()
    for Effect in ("imported", "recomputed", "closed"):
        Evidence = Dispatch.RootPath / f"fixture-control-{Effect}"
        assert JsonCodec.loads(Evidence.read_bytes()) == {"pid": ReplacementPeer["pid"]}
    LoseControl(Dispatch, Flags, Request, Attempt, Result)


# an owner interrupted after native work may reconcile its receipt but may not repeat it
def LoseControl(
    Dispatch: DispatchHost,
    Flags: list[str],
    Request: FilePath,
    Attempt: FilePath,
    Result: FilePath,
) -> None:
    RequestBytes = Request.read_bytes()
    AttemptBytes = Attempt.read_bytes()
    Withheld = Result.with_suffix(".withheld")
    _ = Result.rename(Withheld)
    try:
        with RunOwner(
            Dispatch, [*Flags, "--admit-archived-retry"], "LostControl"
        ) as LogPath:
            Report = AwaitStatus(
                LogPath, "phase_a_probe_archived", Replacement="control_unobserved"
            )
        assert Report["resource_rearmed"] is False
        assert not Result.exists()
        assert Request.read_bytes() == RequestBytes
        assert Attempt.read_bytes() == AttemptBytes
    finally:
        _ = Withheld.rename(Result)


# the independent appkit receipt and bootstrap proof must agree on the new elected pid
def AssertNewPeer(
    Dispatch: DispatchHost,
    LaunchPath: FilePath,
    PeerPath: FilePath,
    StartupPath: FilePath,
    Report: dict[str, object],
) -> None:
    Launch = JsonCodec.loads(LaunchPath.read_bytes())
    PeerBytes = PeerPath.read_bytes()
    FoundPeer = JsonCodec.loads(PeerBytes)
    StartupBytes = StartupPath.read_bytes()
    Startup = JsonCodec.loads(StartupBytes)
    Initial = JsonCodec.loads((Dispatch.Endpoint / "cold-start-peer.json").read_bytes())
    Notice = JsonCodec.loads((Dispatch.RootPath / "ready.json").read_bytes())
    assert FoundPeer["peer"]["pid"] == Notice["pid"] != Initial["peer"]["pid"]
    assert (
        FoundPeer["launch_request_sha256"]
        == HashBytes(LaunchPath.read_bytes()).hexdigest()
    )
    assert Startup["launch_receipt_sha256"] == HashBytes(PeerBytes).hexdigest()
    assert (
        Startup["bootstrap"]["launch_binding_sha256"]
        == HashBytes(Launch["launch_challenge"].encode("ascii")).hexdigest()
    )
    assert (
        Report["archive_replacement_startup_sha256"]
        == HashBytes(StartupBytes).hexdigest()
    )
    assert Report["resource_rearmed"] is False


# an uncertain launch response must stay terminal even while an app is visible
def LoseLaunchReply(
    Dispatch: DispatchHost,
    Enabled: list[str],
    LaunchPath: FilePath,
    PeerPath: FilePath,
    StartupPath: FilePath,
) -> None:
    Prior = LaunchPath.read_bytes()
    StartBytes = StartupPath.read_bytes()
    Withheld = PeerPath.with_suffix(".withheld")
    _ = PeerPath.rename(Withheld)
    try:
        with RunOwner(Dispatch, Enabled, "LostLaunch") as LogPath:
            _ = AwaitStatus(
                LogPath, "phase_a_probe_archived", Replacement="launch_unobserved"
            )
            assert not PeerPath.exists()
    finally:
        _ = Withheld.rename(PeerPath)
    assert LaunchPath.read_bytes() == Prior
    assert StartupPath.read_bytes() == StartBytes


# an observed effect cannot authorize a new launch if its immutable request is missing
def LoseLaunchSeal(
    Dispatch: DispatchHost, Enabled: list[str], LaunchPath: FilePath
) -> None:
    Withheld = LaunchPath.with_suffix(".withheld")
    _ = LaunchPath.rename(Withheld)
    try:
        with RunOwner(Dispatch, Enabled, "LostSeal") as LogPath:
            Refused = AwaitStatus(LogPath, "lifecycle_refused")
            assert Refused["error"] == "ValueError"
            assert not LaunchPath.exists()
    finally:
        _ = Withheld.rename(LaunchPath)
