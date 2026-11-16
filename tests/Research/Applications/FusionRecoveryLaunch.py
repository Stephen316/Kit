import json as JsonCodec
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost
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
    First = Harness.ReadJob(PhaseName)
    assert First["state"] == "waiting_application" and First["attempts"] == 1
    assert Harness.ReadJob("fixture:cold-rival")["attempts"] == 0


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
