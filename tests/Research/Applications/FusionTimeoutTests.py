import json as JsonCodec
import sys as System
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.Research.Applications.FusionPhaseQueueTests import (
    MakeQueueHost,
    RunFusionTool,
)
from tests.Research.SupervisorClient import SessionHost


# a real queued pair provides the phase identity pins used by the recovery audit
def PrepareTimeout(RootPath: FilePath) -> tuple[SessionHost, dict[str, object]]:
    PlanRoot = RootPath / "Prepared"
    Planned = JsonCodec.loads(
        RunFusionTool(
            "re/automation/PairedCaptures/FusionFreshProcess.py",
            ["--output", str(PlanRoot), "--recipe", "P01", "--read-existing"],
        )
    )
    Harness = MakeQueueHost(RootPath, Planned["source_revision"])
    (RootPath / "AbsentEndpoint").mkdir(mode=0o700)
    assert Harness.StorePath is not None
    _ = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:fusion:local",
            "--capacity",
            "1",
            "--available",
        ],
    )
    Queued: dict[str, object] = JsonCodec.loads(
        RunFusionTool(
            "re/automation/ApplicationWorkers/QueueFusionPhases.py",
            [
                "--config",
                str(Harness.ConfigFile),
                "--plan",
                str(PlanRoot / "plan.json"),
                "--resource",
                "application:fusion:local",
            ],
        )
    )
    return Harness, Queued


# a real macos request timeout must preserve exact custody without starting a cad host
@TestMark.skipif(System.platform != "darwin", reason="Fusion worker host boundary")
def CheckFusionWait(TmpPath: FilePath) -> None:
    RootPath = TmpPath.resolve()
    Harness, Queued = PrepareTimeout(RootPath)
    Names = JsonCodec.loads(JsonCodec.dumps(Queued["jobs"]))
    _ = Harness.RunIdle(IdleSeconds=1, MaxSeconds=60)
    Status = Harness.ReadJob(Names["a"])
    assert Status["state"] == "waiting_application", Status
    assert Harness.ReadJob(Names["b"])["state"] == "waiting_evidence"
    Endpoint = RootPath / "AbsentEndpoint"
    Accepted = Harness.ReadResult(Names["a"])
    RequestPath = VerifyTimeout(Endpoint, Accepted, Queued["plan_sha256"])
    VerifyAudit(Harness, Queued, RequestPath)
    VerifyArchive(Harness, RequestPath)


# only the existing owned request can explain the terminal parked attempt
def VerifyTimeout(
    Endpoint: FilePath, Accepted: dict[str, object], PlanHash: object
) -> FilePath:
    (RequestPath,) = Endpoint.glob("jobs/*/probe.request")
    RequestBytes = RequestPath.read_bytes()
    Request = JsonCodec.loads(RequestBytes)
    Result = JsonCodec.loads(JsonCodec.dumps(Accepted["result"]))
    Records = Result["records"]
    assert Records["queue_timeout"] == {
        "version": 1,
        "queue_job_id": RequestPath.parent.name,
        "request_sha256": HashBytes(RequestBytes).hexdigest(),
        "source_revision": Request["source_revision"],
        "operation": "probe",
        "plan_sha256": PlanHash,
    }
    Fence = JsonCodec.loads((Endpoint / "fence.json").read_bytes())
    assert Fence["job_id"] == RequestPath.parent.name
    assert Fence["reason"] == "quarantined"
    assert (RequestPath.parent / "cancel.json").is_file()
    assert Records["native_qualified"] is False
    assert "output_artifacts" not in Accepted
    assert "application_rearm_intent_sha256" not in Accepted
    return RequestPath


# the read only audit must bind the parked result and the original spool bytes
def VerifyAudit(
    Harness: SessionHost, Queued: dict[str, object], RequestPath: FilePath
) -> None:
    assert Harness.StorePath is not None
    QueuePath = Harness.RootPath / "TimedQueue.json"
    _ = QueuePath.write_text(JsonCodec.dumps(Queued), encoding="utf-8")
    ScriptPath = "re/automation/ApplicationWorkers/AuditFusionPhases.py"
    Arguments = [
        "--store",
        str(Harness.StorePath),
        "--queue-receipt",
        str(QueuePath),
        "--installation",
        str(Harness.RootPath / "Installation.json"),
    ]
    Report = JsonCodec.loads(RunFusionTool(ScriptPath, Arguments))
    Phase = Report["phases"]["a"]
    assert Report["status"] == "pending" and Report["resource_available"] is False
    assert Phase["spool_observation"] == {
        "status": "request",
        "fence_status": "quarantined",
    }
    RequestBytes = RequestPath.read_bytes()
    assert (
        Phase["queue_timeout"]["request_sha256"] == HashBytes(RequestBytes).hexdigest()
    )
    _ = RequestPath.write_bytes(RequestBytes + b" ")
    _ = RunFusionTool(ScriptPath, Arguments, ExitCode=1)
    _ = RequestPath.write_bytes(RequestBytes)


# an ownership refusal must preserve the requesting spool and its exact fence
def VerifyRefusal(
    ArchivePath: str, Arguments: list[str], SpoolPath: FilePath, FencePath: FilePath
) -> None:
    import fcntl as FileLocks

    FenceBytes = FencePath.read_bytes()
    Fence = JsonCodec.loads(FenceBytes)
    Fence["reason"] = "acceptance_required"
    HeldBytes = JsonCodec.dumps(Fence).encode("utf-8")
    _ = FencePath.write_bytes(HeldBytes)
    _ = RunFusionTool(ArchivePath, Arguments, ExitCode=1)
    assert FencePath.read_bytes() == HeldBytes
    assert SpoolPath.is_dir()
    _ = FencePath.write_bytes(FenceBytes)
    with (FencePath.parent / "host.lock").open("ab") as LockFile:
        FileLocks.flock(LockFile.fileno(), FileLocks.LOCK_EX | FileLocks.LOCK_NB)
        _ = RunFusionTool(ArchivePath, Arguments, ExitCode=1)
        assert FencePath.read_bytes() == FenceBytes
        assert SpoolPath.is_dir()


# an interrupted fence release can retry from the archived bytes without rearming the store
def VerifyReplay(
    ArchivePath: str, Arguments: list[str], FencePath: FilePath, FenceBytes: bytes
) -> None:
    Retry = JsonCodec.loads(RunFusionTool(ArchivePath, Arguments))
    assert Retry["status"] == "already_archived" and not FencePath.exists()
    _ = FencePath.write_bytes(FenceBytes)
    Resumed = JsonCodec.loads(RunFusionTool(ArchivePath, Arguments))
    assert Resumed["status"] == "archive_resumed" and not FencePath.exists()
    assert Resumed["archive_manifest_sha256"] == Retry["archive_manifest_sha256"]


# the archival receipt and unchanged controller prove the limits of the owner action
def VerifyArchive(Harness: SessionHost, RequestPath: FilePath) -> None:
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    StoreHash = HashBytes(DatabasePath.read_bytes()).hexdigest()
    ArchivePath = "re/automation/ApplicationWorkers/ArchiveFusionProbe.py"
    Arguments = [
        "--config",
        str(Harness.ConfigFile),
        "--queue-receipt",
        str(Harness.RootPath / "TimedQueue.json"),
    ]
    SpoolPath = RequestPath.parent
    Endpoint = Harness.RootPath / "AbsentEndpoint"
    FencePath = Endpoint / "fence.json"
    VerifyRefusal(ArchivePath, Arguments, SpoolPath, FencePath)
    FenceBytes = FencePath.read_bytes()
    Retained = {
        EntryPath.name: EntryPath.read_bytes() for EntryPath in SpoolPath.iterdir()
    }
    Result = JsonCodec.loads(RunFusionTool(ArchivePath, Arguments))
    assert Result["status"] == "archived" and Result["resource_rearmed"] is False
    assert not SpoolPath.exists() and not FencePath.exists()
    SavedPath = Endpoint / "failed-spools" / SpoolPath.name
    for FileName, Content in Retained.items():
        assert (SavedPath / FileName).read_bytes() == Content
    Manifest = SavedPath / "ProbeArchive.json"
    assert (
        HashBytes(Manifest.read_bytes()).hexdigest()
        == Result["archive_manifest_sha256"]
    )
    VerifyReplay(ArchivePath, Arguments, FencePath, FenceBytes)
    assert HashBytes(DatabasePath.read_bytes()).hexdigest() == StoreHash
