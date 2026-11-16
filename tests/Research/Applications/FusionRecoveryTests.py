import json as JsonCodec
import sys as System
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.FusionColdStartTests import (
    KFixtureTool,
    PrepareCold,
    RunInitialOwner,
)
from tests.Research.Applications.FusionColdWatch import AwaitStatus, RunOwner
from tests.Research.Applications.FusionPhaseQueueTests import RunFusionTool
from tests.Research.SupervisorClient import SessionHost


# an actual supervisor timeout and independent kernel watch must join without releasing the resource
@TestMark.skipif(
    System.platform != "darwin", reason="macOS archived native exit custody"
)
def CheckRecovery(TmpPath: FilePath) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Flags, PhaseName = PrepareCold(Dispatch)
    try:
        Admitted = RunInitialOwner(Dispatch, Flags)
        assert Admitted["job"] == PhaseName
        assert Admitted["status"] == "initial_phase_a_admission_recorded"
        AdmissionHash = Admitted["evidence_sha256"]
        with RunOwner(Dispatch, Flags, "RecoveryOwner") as LogPath:
            _ = AwaitStatus(LogPath, "commissioned_exit_watch_armed")
            _ = RunFusionTool(
                KFixtureTool,
                ["cleanup", str(Dispatch.RootPath), str(Dispatch.Endpoint)],
            )
            Exited = AwaitStatus(LogPath, "commissioned_native_exit_observed")
            assert Exited["disposition"] == "outside_owner_scheduled_quit"
            ExitPath = Dispatch.Endpoint / f"initial-native-exit-{AdmissionHash}.json"
            AwaitArchive(Dispatch, Harness, PhaseName, LogPath, ExitPath)
    finally:
        _ = RunFusionTool(
            KFixtureTool, ["cleanup", str(Dispatch.RootPath), str(Dispatch.Endpoint)]
        )


# withholding the real exit receipt must leave the durable archive safely parked
def AwaitArchive(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    PhaseName: str,
    LogPath: FilePath,
    ExitPath: FilePath,
) -> None:
    Withheld = ExitPath.with_suffix(".withheld")
    _ = ExitPath.rename(Withheld)
    try:
        _ = Harness.RunIdle(IdleSeconds=1, MaxSeconds=60)
        Missing = AwaitStatus(
            LogPath, "phase_a_probe_archived", "commissioned_exit_missing"
        )
        assert Missing["resource_rearmed"] is False
        assert not list(Dispatch.Endpoint.glob("archived-recovery-basis-*.json"))
        assert Harness.ReadJob(PhaseName)["state"] == "waiting_application"
    finally:
        _ = Withheld.rename(ExitPath)
    Verified = AwaitStatus(
        LogPath, "phase_a_probe_archived", "sealed_for_replacement_preflight"
    )
    VerifyBasis(Dispatch, Harness, PhaseName, ExitPath, Verified)


# only the original attempt and its exact request may appear in the joined record
def VerifyBasis(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    PhaseName: str,
    ExitPath: FilePath,
    Verified: dict[str, object],
) -> None:
    ArchiveHash = Verified["archive_manifest_sha256"]
    BasisPath = Dispatch.Endpoint / f"archived-recovery-basis-{ArchiveHash}.json"
    RawBytes = BasisPath.read_bytes()
    Basis = JsonCodec.loads(RawBytes)
    First = Harness.ReadJob(PhaseName)
    (Manifest,) = (Dispatch.Endpoint / "failed-spools").glob("*/ProbeArchive.json")
    Archive = JsonCodec.loads(Manifest.read_bytes())
    assert Verified["recovery_basis_sha256"] == HashBytes(RawBytes).hexdigest()
    assert (
        Basis["archive_manifest_sha256"] == HashBytes(Manifest.read_bytes()).hexdigest()
    )
    assert (
        Basis["commissioned_exit_sha256"]
        == HashBytes(ExitPath.read_bytes()).hexdigest()
    )
    assert Basis["request_sha256"] == Archive["timeout"]["request_sha256"]
    assert Basis["first_receipt_sha256"] == First["receipt"]
    assert Basis["first_result_sha256"] == First["result"]
    assert Basis["first_attempt"] == First["attempts"] == 1
    assert Basis["epoch"]["generation"] == First["generation"]
    assert Basis["epoch"]["fingerprint"] == First["fingerprint"]
    assert Verified["resource_rearmed"] is False
    assert First["state"] == "waiting_application"
    assert Harness.ReadJob("fixture:cold-rival")["attempts"] == 0
