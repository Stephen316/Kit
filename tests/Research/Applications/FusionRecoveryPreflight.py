import json as JsonCodec
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.FusionColdWatch import AwaitStatus
from tests.Research.Applications.FusionPhaseQueueTests import RunFusionTool
from tests.Research.SupervisorClient import SessionHost


# a changed challenge cannot replace the one binding derived from the genuine commissioning
def VerifyPreflight(
    Dispatch: DispatchHost, LogPath: FilePath, Verified: dict[str, object]
) -> FilePath:
    ArchiveHash = Verified["archive_manifest_sha256"]
    SlotPath = Dispatch.Endpoint / f"archived-replacement-preflight-{ArchiveHash}.json"
    Original = SlotPath.read_bytes()
    Binding = JsonCodec.loads(Original)
    ColdPath = Dispatch.Endpoint / "cold-start-request.json"
    ColdProof = ColdPath.read_bytes()
    ColdLaunch = (Dispatch.Endpoint / "cold-start-launch.json").read_bytes()
    assert Verified["replacement_preflight_status"] == "sealed"
    assert Verified["replacement_preflight_sha256"] == HashBytes(Original).hexdigest()
    assert Binding["recovery_basis_sha256"] == Verified["recovery_basis_sha256"]
    assert Binding["archive_manifest_sha256"] == ArchiveHash
    assert Binding["launch_challenge"] != JsonCodec.loads(ColdProof)["launch_challenge"]
    RefuseForeign(SlotPath, LogPath, Original)
    RefuseCold(ColdPath, LogPath, SlotPath, Original)
    assert ColdPath.read_bytes() == ColdProof
    assert (Dispatch.Endpoint / "cold-start-launch.json").read_bytes() == ColdLaunch
    assert not list(Dispatch.Endpoint.glob("replacement-launch-*.json"))
    return SlotPath


# a validly shaped substitute challenge must never replace the derived challenge
def RefuseForeign(SlotPath: FilePath, LogPath: FilePath, Original: bytes) -> None:
    Binding = JsonCodec.loads(Original)
    Foreign = "0" * 48
    if Foreign == Binding["launch_challenge"]:
        Foreign = "1" * 48
    ForeignBytes = JsonCodec.dumps({**Binding, "launch_challenge": Foreign}).encode(
        "utf-8"
    )
    _ = SlotPath.write_bytes(ForeignBytes)
    try:
        Conflict = AwaitStatus(
            LogPath, "phase_a_probe_archived", Preflight="replacement_binding_conflict"
        )
        assert "replacement_preflight_sha256" not in Conflict
        assert Conflict["resource_rearmed"] is False
        assert SlotPath.read_bytes() == ForeignBytes
    finally:
        _ = SlotPath.write_bytes(Original)


# changing the original commissioning receipt must fail independent of the slot digest
def RefuseCold(
    ColdPath: FilePath, LogPath: FilePath, SlotPath: FilePath, Original: bytes
) -> None:
    ColdBytes = ColdPath.read_bytes()
    ColdProof = JsonCodec.loads(ColdBytes)
    ColdProof["admission"]["generation"] += 1
    _ = ColdPath.write_bytes(JsonCodec.dumps(ColdProof).encode("utf-8"))
    try:
        Refused = AwaitStatus(
            LogPath,
            "phase_a_probe_archived",
            Preflight="commissioned_deployment_unverified",
        )
        assert "replacement_preflight_sha256" not in Refused
        assert SlotPath.read_bytes() == Original
    finally:
        _ = ColdPath.write_bytes(ColdBytes)


# normal controller generation invalidation must render the prior sealed replacement unusable
def RefuseNewEpoch(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Flags: list[str],
    PhaseName: str,
    PreflightPath: FilePath,
) -> None:
    Original = PreflightPath.read_bytes()
    Previous = Harness.ReadJob(PhaseName)
    Queue = JsonCodec.loads((Dispatch.RootPath / "ColdPair.json").read_bytes())
    Harness.BindBytes(Queue["plan_binding"], b"foreign plan input")
    Current = Harness.ReadJob(PhaseName)
    assert Current["generation"] != Previous["generation"]
    assert Current["attempts"] == 0 and Current["state"] == "waiting_application"
    Output = RunFusionTool(
        "re/automation/ApplicationWorkers/FusionLifecycleOwner.py",
        [*Flags, "--queue-directory", str(Dispatch.RootPath), "--once"],
        ExitCode=1,
    )
    assert Output == ""
    assert PreflightPath.read_bytes() == Original
    assert not list(Dispatch.Endpoint.glob("replacement-launch-*.json"))
