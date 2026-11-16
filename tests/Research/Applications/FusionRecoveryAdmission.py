import json as JsonCodec
import shutil as FileCopies
import sqlite3 as SqliteDb
from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.FusionColdWatch import AwaitStatus, RunOwner
from tests.Research.Applications.FusionPhaseQueueTests import RunFusionTool
from tests.Research.SupervisorClient import SessionHost


# the isolated store command exercises actual controller admission claim and settlement
def ControllerRun(StorePath: FilePath, *Arguments: str) -> dict[str, object]:
    Record: dict[str, object] = JsonCodec.loads(
        RunFusionTool(
            "re/automation/Controller.py", ["--store", str(StorePath), *Arguments]
        )
    )
    return Record


# keep the controlling transaction observable independently of owner process output
def ArchiveEvents(StorePath: FilePath) -> list[dict[str, object]]:
    History = ControllerRun(StorePath, "events")
    Events = CastValue(list[dict[str, object]], History["events"])
    return [
        JsonCodec.loads(str(Event["detail"]))
        for Event in Events
        if Event["action"] == "fusion_archived_retry_admitted"
    ]


# the same owner flags must be used for initial admission and the later refusal checks
def RetryOptions(Flags: list[str]) -> list[str]:
    return [
        *Flags,
        "--launch-archived-replacement",
        "--measure-archived-replacement",
        "--admit-archived-retry",
    ]


# a foreign generation cannot run the exact owner admission again
def RefuseReadmit(Dispatch: DispatchHost, Flags: list[str]) -> None:
    Result = RunFusionTool(
        "re/automation/ApplicationWorkers/FusionLifecycleOwner.py",
        [*RetryOptions(Flags), "--queue-directory", str(Dispatch.RootPath)],
        ExitCode=1,
    )
    assert Result == ""


# the exact control can be recovered once and commit only the reserved second attempt
def VerifyAdmission(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Flags: list[str],
    PhaseName: str,
    Archive: dict[str, object],
) -> dict[str, object]:
    StorePath = Harness.StorePath
    assert StorePath is not None
    Initial = Harness.ReadJob(PhaseName)
    assert Initial["state"] == "waiting_application" and Initial["attempts"] == 1
    Enabled = RetryOptions(Flags)
    with RunOwner(Dispatch, Enabled, "AdmitRetry") as LogPath:
        Report = AwaitStatus(
            LogPath,
            "phase_a_archive_retry_admitted",
            Replacement="retry_admitted",
            WaitSeconds=30,
        )
    assert Report["resource_rearmed"] is True
    assert Report["archive_replacement_admission_attempt"] == 2
    Pending = Harness.ReadJob(PhaseName)
    assert Pending["state"] == "queued" and Pending["attempts"] == 1
    (Accepted,) = ArchiveEvents(StorePath)
    VerifyArtifacts(StorePath, Archive, Initial, Report, Accepted)
    CopyPath = Dispatch.RootPath / "RetryStore"
    _ = FileCopies.copytree(StorePath, CopyPath)
    FinishRetry(CopyPath, Dispatch.RootPath, PhaseName)
    ExpireLease(StorePath, Dispatch.RootPath, PhaseName)
    with RunOwner(Dispatch, Enabled, "ResumeAdmitted") as LogPath:
        _ = AwaitStatus(LogPath, "waiting_for_acknowledged_phase_a")
    assert ArchiveEvents(StorePath) == [Accepted]
    return Accepted


# the evidence in the controller must remain reconstructable after the owner exits
def VerifyArtifacts(
    StorePath: FilePath,
    Archive: dict[str, object],
    Initial: dict[str, object],
    Report: dict[str, object],
    Accepted: dict[str, object],
) -> None:
    assert Accepted["archive_manifest_sha256"] == Archive["archive_manifest_sha256"]
    assert Accepted["first_receipt_sha256"] == Initial["receipt"]
    assert Accepted["first_result_sha256"] == Initial["result"]
    assert Accepted["generation"] == Initial["generation"]
    assert Accepted["fingerprint"] == Initial["fingerprint"]
    assert Accepted["next_attempt"] == 2
    assert Accepted["control_sha256"] == Report["archive_replacement_control_sha256"]
    for RecordName in (
        "control",
        "control_request",
        "control_attempt",
        "process",
        "startup",
    ):
        Digest = str(Accepted[f"{RecordName}_sha256"])
        Artifact = StorePath / "objects" / Digest[:2] / Digest
        assert HashBytes(Artifact.read_bytes()).hexdigest() == Digest


# retrying a settled second lease consumes the automatic budget on the original definition
def FinishRetry(StorePath: FilePath, RootPath: FilePath, PhaseName: str) -> None:
    LeasePath = RootPath / "FinishSecond.json"
    ClaimSecond(StorePath, LeasePath, PhaseName)
    ResultPath = RootPath / "RetryResult.json"
    _ = ResultPath.write_text("{}", encoding="utf-8")
    _ = ControllerRun(
        StorePath,
        "finish",
        "--lease",
        str(LeasePath),
        "--result",
        str(ResultPath),
        "--outcome",
        "retry",
        "--reason",
        "synthetic transport retry after exact admission",
    )
    AssertSpent(StorePath, RootPath / "AfterRetry.json", PhaseName)


# an expired second lease must fail closed and must not admit the rival after administrative availability
def ExpireLease(StorePath: FilePath, RootPath: FilePath, PhaseName: str) -> None:
    ClaimSecond(StorePath, RootPath / "ExpireSecond.json", PhaseName)
    Connection = SqliteDb.connect(StorePath / "ledger.sqlite3")
    try:
        with Connection:
            Updated = Connection.execute(
                "UPDATE jobs SET lease_until=0 WHERE id=? AND state='running'",
                (PhaseName,),
            )
            assert Updated.rowcount == 1
    finally:
        Connection.close()
    AssertSpent(StorePath, RootPath / "AfterExpiry.json", PhaseName)
    _ = ControllerRun(StorePath, "resource", "application:fusion:local", "--available")
    AssertSpent(StorePath, RootPath / "AfterEnable.json", PhaseName)
    _ = ControllerRun(
        StorePath, "resource", "application:fusion:local", "--unavailable"
    )


# actual single admission must select the reserved job before older competing work
def ClaimSecond(StorePath: FilePath, LeasePath: FilePath, PhaseName: str) -> None:
    Claimed = ControllerRun(
        StorePath,
        "claim",
        "--worker",
        "fixture:archive",
        "--claim-file",
        str(LeasePath),
    )
    assert Claimed["job"] == PhaseName and Claimed["attempt"] == 2


# terminal budget and rival exclusion must remain true across new claimant processes
def AssertSpent(StorePath: FilePath, ClaimPath: FilePath, PhaseName: str) -> None:
    Terminal = ControllerRun(StorePath, "status", "--job", PhaseName)
    (JobRow,) = CastValue(list[dict[str, object]], Terminal["jobs"])
    assert JobRow["state"] == "failed" and JobRow["attempts"] == 2
    Claimed = ControllerRun(
        StorePath, "claim", "--worker", "fixture:third", "--claim-file", str(ClaimPath)
    )
    assert Claimed["job"] is None and not ClaimPath.exists()
