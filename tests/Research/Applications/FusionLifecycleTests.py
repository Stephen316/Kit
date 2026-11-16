import json as JsonCodec
import sqlite3 as SqlCodec
import subprocess as Subprocess
import sys as System
from contextlib import closing as CloseConnection
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionOwnerRestartTests import SelectFixture
from tests.Research.Applications.FusionPhaseQueueTests import (
    MakeQueueHost,
    PreparePair,
    RunFusionTool,
)
from tests.Research.Applications.RunQueueHost import RunQueueHost
from tests.Research.SupervisorClient import FixtureJob, SessionHost

# the disposable provider hosts the actual owner cli in a separate process
KLifecycleTool = (
    KRepoRoot / "re/automation/ApplicationWorkers/FusionLifecycleFixture.py"
)


# the driver must recover the actual durable paired queue after accepted phase a
def PrepareCycle(
    Dispatch: DispatchHost, ReservePair: bool = False
) -> tuple[SessionHost, FilePath, bytes]:
    Output = Dispatch.RootPath / "Prepared"
    PlanInfo = PreparePair(Output, False)
    Harness = MakeQueueHost(Dispatch.RootPath, PlanInfo["source_revision"])
    Install = JsonCodec.loads(Dispatch.ConfigFile.read_bytes())
    Install.update(endpoint=str(Dispatch.Endpoint), macos_automatic_quit=True)
    _ = Dispatch.ConfigFile.write_text(JsonCodec.dumps(Install), encoding="utf-8")
    Inbox = Dispatch.RootPath / "Inbox"
    Inbox.mkdir(mode=0o700)
    Receipt = Inbox / "Queue.json"
    if ReservePair:
        QueueRivals(Harness)
    _ = RunFusionTool(
        "re/automation/ApplicationWorkers/QueueFusionPhases.py",
        [
            "--config",
            str(Harness.ConfigFile),
            "--plan",
            str(Output / "plan.json"),
            "--resource",
            "application:fusion:local",
            "--receipt",
            str(Receipt),
        ]
        + (["--owner-lifecycle"] if ReservePair else []),
    )
    Registry = (Dispatch.RootPath / "Runners.json").read_bytes()
    SelectFixture(Dispatch, Harness)
    return Harness, Receipt, Registry


# the older contenders become runnable only after the accepted phase establishes custody
def QueueRivals(Harness: SessionHost) -> None:
    Harness.SubmitJobs(
        [
            FixtureJob(
                NameValue,
                "capture.fusion",
                resources=["application:fusion:local"],
                inputs={"source": "fixture:rival-input"},
            )
            for NameValue in ("fixture:rival-first", "fixture:rival-second")
        ]
    )


# true controller settlement and spool acknowledgement precede phase admission
def AcceptFirst(
    Dispatch: DispatchHost, Harness: SessionHost, Receipt: FilePath, Registry: bytes
) -> tuple[str, FilePath]:
    JobNames = CastValue(dict[str, str], JsonCodec.loads(Receipt.read_bytes())["jobs"])
    _ = Harness.RunIdle()
    assert Harness.ReadJob(JobNames["a"])["state"] == "completed"
    assert Harness.ReadJob(JobNames["b"])["state"] == "waiting_application"
    assert (
        AdvanceCycle(Dispatch, Harness, Receipt, "resume")["status"]
        == "waiting_for_acknowledged_phase_a"
    )
    assert Harness.StorePath is not None
    Acknowledgement = RunFusionTool(
        "re/automation/ApplicationWorkers/AcknowledgeApplication.py",
        [
            "--installation",
            str(Dispatch.ConfigFile),
            "--store",
            str(Harness.StorePath),
            "--job",
            JobNames["a"],
        ],
    )
    assert JsonCodec.loads(Acknowledgement)["restart_retained"] is True
    _ = (Dispatch.RootPath / "Runners.json").write_bytes(Registry)
    Receipt.unlink()
    return JobNames["b"], Dispatch.RootPath / "PhaseBClaim.json"


# only the real controller can grant the second fixture attempt
def ClaimSecond(Harness: SessionHost, JobName: str, Claim: FilePath) -> None:
    Prefix = ["--store", str(Harness.StorePath)]
    _ = RunFusionTool(
        "re/automation/Controller.py",
        Prefix
        + ["resource", "application:fusion:local", "--capacity", "1", "--available"],
    )
    _ = RunFusionTool(
        "re/automation/Controller.py",
        Prefix + ["claim", "--worker", "fixture:lifecycle", "--claim-file", str(Claim)],
    )
    assert Harness.ReadJob(JobName)["state"] == "running"


# each call starts a fresh owner so simulated response loss cannot retain process state
def AdvanceCycle(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Receipt: FilePath,
    ModeName: str,
    ExitCode: int = 0,
    Replacement: int = 0,
) -> dict[str, object]:
    LifecyclePath = Receipt.parent / "Lifecycle.json"
    if not LifecyclePath.exists():
        _ = LifecyclePath.write_text("disposable lifecycle profile\n", encoding="utf-8")
    Process = Subprocess.run(
        [
            System.executable,
            "-B",
            str(KLifecycleTool),
            ModeName,
            str(Replacement),
            "--config",
            str(Harness.ConfigFile),
            "--installation",
            str(Dispatch.ConfigFile),
            "--lifecycle",
            str(LifecyclePath),
            "--queue-directory",
            str(Receipt.parent),
            "--wait-seconds",
            "10",
            "--once",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == ExitCode, Process.stderr + Process.stdout
    return (
        CastValue(dict[str, object], JsonCodec.loads(Process.stdout))
        if Process.stdout
        else {}
    )


# the actual quit request is never repeated after an interrupted owner loses its result
@TestMark.skipif(System.platform != "darwin", reason="exact Darwin exit custody")
@TestMark.parametrize(
    ("ModeName", "Expected", "ExitCode"),
    (
        ("quit-lost", "quit_exit_unobserved", 73),
        ("lease-expired", "phase_b_ineligible", 1),
    ),
)
def CheckQuitResume(
    TmpPath: FilePath, ModeName: str, Expected: str, ExitCode: int
) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Receipt, Registry = PrepareCycle(Dispatch)
    with RunQueueHost(Dispatch, "owner-restart-host"):
        PhaseB, Claim = AcceptFirst(Dispatch, Harness, Receipt, Registry)
        assert (
            AdvanceCycle(Dispatch, Harness, Receipt, "resume")["status"]
            == "phase_b_ineligible"
        )
        assert not list(Dispatch.Endpoint.glob("quit-request-*.json"))
        ClaimSecond(Harness, PhaseB, Claim)
        _ = AdvanceCycle(Dispatch, Harness, Receipt, ModeName, ExitCode)
        assert Receipt.is_file()
        Requests = list(Dispatch.Endpoint.glob("quit-request-*.json"))
        assert len(Requests) == int(ModeName == "quit-lost")
        Status = AdvanceCycle(Dispatch, Harness, Receipt, "resume")
        assert Status["status"] == Expected
        assert list(Dispatch.Endpoint.glob("quit-request-*.json")) == Requests
        assert not list(Dispatch.Endpoint.glob("replacement-launch-*.json"))
        assert (Dispatch.Endpoint / "fence.json").is_file()


# an observed kernel exit supports once only replacement and durable final recovery
@TestMark.skipif(System.platform != "darwin", reason="exact Darwin exit custody")
@TestMark.parametrize("ModeName", ("launch-lost", "launch-exit"))
def CheckLaunchOnce(TmpPath: FilePath, ModeName: str) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Receipt, Registry = PrepareCycle(Dispatch)
    with RunQueueHost(Dispatch, "owner-restart-host"):
        PhaseB, Claim = AcceptFirst(Dispatch, Harness, Receipt, Registry)
        ClaimSecond(Harness, PhaseB, Claim)
        _ = AdvanceCycle(Dispatch, Harness, Receipt, "exit-lost", 73)
        assert len(list(Dispatch.Endpoint.glob("quit-exit-*.json"))) == 1
    ExerciseLaunch(Dispatch, Harness, Receipt, PhaseB, Claim, ModeName)


# track the exact disposable replacement independently of either owner command invocation
def ExerciseLaunch(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Receipt: FilePath,
    PhaseB: str,
    Claim: FilePath,
    ModeName: str,
    ExpectHold: bool = False,
) -> None:
    Child = Subprocess.Popen(
        [
            System.executable,
            "-B",
            "-c",
            "import sys; print('ready', flush=True); sys.stdin.readline()",
        ],
        stdin=Subprocess.PIPE,
        stdout=Subprocess.PIPE,
        text=True,
    )
    try:
        assert Child.stdout is not None and Child.stdout.readline() == "ready\n"
        _ = AdvanceCycle(Dispatch, Harness, Receipt, ModeName, 73, Child.pid)
        Launch = list(Dispatch.Endpoint.glob("replacement-launch-*.json"))
        assert len(Launch) == 1
        LaunchBytes = Launch[0].read_bytes()
        Status = AdvanceCycle(Dispatch, Harness, Receipt, "resume")
        assert Launch[0].read_bytes() == LaunchBytes
        if ModeName == "launch-lost":
            assert Status["status"] == "replacement_unobserved"
            assert (Dispatch.Endpoint / "fence.json").is_file()
        else:
            assert Status["status"] == "waiting_for_phase_b"
            FinishCycle(
                Dispatch, Harness, Receipt, PhaseB, Claim, Child.pid, ExpectHold
            )
    finally:
        _ = Child.communicate("\n", timeout=5)
        assert Child.returncode == 0


# finalized evidence must survive an interrupted reply without calling the phase verifier twice
def FinishCycle(
    Dispatch: DispatchHost,
    Harness: SessionHost,
    Receipt: FilePath,
    PhaseB: str,
    Claim: FilePath,
    PeerPid: int,
    ExpectHold: bool = False,
) -> None:
    Result = Dispatch.RootPath / "PhaseBResult.json"
    ReceiptData: dict[str, object] = {"fixture": True}
    if ExpectHold:
        ReceiptData.update(
            receipt={"session": "a-12345678"},
            application_acknowledgement_sha256="d" * 64,
        )
    _ = Result.write_text(JsonCodec.dumps(ReceiptData), encoding="utf-8")
    _ = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "finish",
            "--lease",
            str(Claim),
            "--result",
            str(Result),
            "--outcome",
            "completed",
            "--reason",
            "disposable",
        ],
    )
    if ExpectHold:
        AssertClaimable(Harness, None)
    _ = AdvanceCycle(Dispatch, Harness, Receipt, "final-lost", 73, PeerPid)
    Active = Dispatch.Endpoint / "fusion-lifecycle-active.json"
    assert Active.is_file()
    if ExpectHold:
        AssertClaimable(Harness, None)
    Status = AdvanceCycle(Dispatch, Harness, Receipt, "resume")
    assert Status["status"] == "lifecycle_verified"
    PhaseInfo = CastValue(dict[str, object], Status["phase_b"])
    PeerInfo = CastValue(dict[str, object], PhaseInfo["peer"])
    assert PhaseInfo["phase_b_receipt_sha256"] == Harness.ReadJob(PhaseB)["receipt"]
    assert PeerInfo["pid"] == PeerPid
    assert PhaseInfo["native_qualified"] is False
    assert not Active.exists()


# a real claim response proves whether a runnable contender can take the held installation
def AssertClaimable(Harness: SessionHost, Expected: str | None) -> None:
    Destination = Harness.RootPath / "ContendingClaim.json"
    Output = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "claim",
            "--worker",
            "fixture:contender",
            "--claim-file",
            str(Destination),
        ],
    )
    assert JsonCodec.loads(Output)["job"] == Expected
    assert Destination.is_file() == (Expected is not None)


# an interrupted supervisor has committed phase a without performing acknowledgement
def StopAfterFirst(Dispatch: DispatchHost, Harness: SessionHost) -> None:
    RunnerPath = Dispatch.RootPath / "Runners.json"
    Runners = JsonCodec.loads(RunnerPath.read_bytes())
    Runners["runners"]["capture.fusion"]["application_installation"] = str(
        Dispatch.ConfigFile
    )
    _ = RunnerPath.write_text(JsonCodec.dumps(Runners), encoding="utf-8")
    Process = Subprocess.run(
        [
            System.executable,
            "-B",
            str(KLifecycleTool),
            "acceptance-crash",
            "--config",
            str(Harness.ConfigFile),
            "run",
            "--idle-seconds",
            "3",
            "--max-seconds",
            "50",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 74, Process.stdout + Process.stderr


# the installed priority lane must ignore requested work blocked by the same reservation
def InstallGrid(Harness: SessionHost, PhaseB: str) -> None:
    assert Harness.StorePath is not None
    with CloseConnection(
        SqlCodec.connect(Harness.StorePath / "ledger.sqlite3")
    ) as DbRead:
        JobSpecs = [
            JsonCodec.loads(
                DbRead.execute(
                    "SELECT definition FROM jobs WHERE id=?", (JobName,)
                ).fetchone()[0]
            )
            for JobName in (PhaseB, "fixture:rival-first")
        ]
    Priorities: list[dict[str, object]] = [
        {
            "id": SpecInfo["id"],
            "family": "fixture",
            "documents": [],
            "distinguishing_evidence": [],
            "installation": "application:fusion:local",
            "grid": GridKind,
        }
        for SpecInfo, GridKind in zip(JobSpecs, ("standard", "requested"), strict=True)
    ]
    PlanPath = Harness.RootPath / "GridPlan.json"
    _ = PlanPath.write_text(
        JsonCodec.dumps(
            {"schedule_version": 1, "jobs": JobSpecs, "priority": Priorities}
        ),
        encoding="utf-8",
    )
    _ = RunFusionTool(
        "re/automation/Controller.py",
        ["--store", str(Harness.StorePath), "schedule", str(PlanPath)],
    )


# neither an unacknowledged hold nor a single admitted phase may form a runnable group
def AssertNoGroup(Harness: SessionHost) -> None:
    Registry = Harness.RootPath / "GroupRegistry.json"
    _ = Registry.write_text(
        '{"group_registry_version":1,"kinds":{"capture.fusion":16777216}}',
        encoding="utf-8",
    )
    Destination = Harness.RootPath / "RivalGroup"
    Reply = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "claim-group",
            "--worker",
            "fixture:contender",
            "--pool",
            "fusion",
            "--registry",
            str(Registry),
            "--claim-dir",
            str(Destination),
        ],
    )
    assert JsonCodec.loads(Reply)["count"] == 0
    assert not Destination.exists()


# the older timeout hold uses the actual a03 terminal path on a different installation
def AddTimeoutHold(Harness: SessionHost) -> dict[str, object]:
    Process = Subprocess.run(
        [
            System.executable,
            "-B",
            str(KLifecycleTool),
            "legacy-timeout",
            str(Harness.StorePath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    return CastValue(dict[str, object], JsonCodec.loads(Process.stdout))


# neither activation nor final release can erase another installation timeout epoch
def AssertTimeout(Harness: SessionHost, Original: dict[str, object]) -> None:
    assert Harness.StorePath is not None
    with CloseConnection(
        SqlCodec.connect(Harness.StorePath / "ledger.sqlite3")
    ) as DbRead:
        HoldRow = DbRead.execute(
            "SELECT resource,epoch,job_id,receipt,result FROM application_holds WHERE resource=?",
            (Original["resource"],),
        ).fetchone()
    KeysHeld = ("resource", "epoch", "job_id", "receipt", "result")
    assert dict(zip(KeysHeld, HoldRow, strict=True)) == Original
    assert Harness.ReadJob("fixture:legacy")["state"] == "waiting_application"


# the older grid candidate cannot park fusion during either handoff or final proof recovery
@TestMark.skipif(
    System.platform != "darwin", reason="macOS restart policy and endpoint custody"
)
@TestMark.parametrize("CaseName", ("complete", "invalidated"))
def CheckReserve(TmpPath: FilePath, CaseName: str) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Receipt, Registry = PrepareCycle(Dispatch, True)
    QueueInfo = JsonCodec.loads(Receipt.read_bytes())
    PhaseB = CastValue(str, QueueInfo["jobs"]["b"])
    Claim = Dispatch.RootPath / "ReservedClaim.json"
    with RunQueueHost(Dispatch, "owner-restart-host"):
        StopAfterFirst(Dispatch, Harness)
        TimeoutProof = AddTimeoutHold(Harness) if CaseName == "complete" else {}
        assert Harness.ReadJob(QueueInfo["jobs"]["a"])["state"] == "completed"
        Harness.BindBytes("fixture:rival-input", b"runnable competitor")
        AssertClaimable(Harness, None)
        AssertNoGroup(Harness)
        RecoverFirst(Dispatch, Harness, Receipt, Registry)
        if CaseName == "invalidated":
            Harness.BindBytes(QueueInfo["plan_binding"], b"replaced plan")
            AssertClaimable(Harness, None)
            assert (
                AdvanceCycle(Dispatch, Harness, Receipt, "resume", 1)["status"]
                == "lifecycle_refused"
            )
            return
        InstallGrid(Harness, PhaseB)
        AssertNoGroup(Harness)
        ClaimSecond(Harness, PhaseB, Claim)
        _ = AdvanceCycle(Dispatch, Harness, Receipt, "exit-lost", 73)
    ExerciseLaunch(Dispatch, Harness, Receipt, PhaseB, Claim, "launch-exit", True)
    AssertClaimable(Harness, "fixture:rival-first")
    AssertTimeout(Harness, TimeoutProof)


# a replacement supervisor drains the accepted spool before the owner opens the reserved phase
def RecoverFirst(
    Dispatch: DispatchHost, Harness: SessionHost, Receipt: FilePath, Registry: bytes
) -> None:
    assert (
        AdvanceCycle(Dispatch, Harness, Receipt, "resume")["status"]
        == "waiting_for_acknowledged_phase_a"
    )
    _ = Harness.RunIdle()
    _ = (Dispatch.RootPath / "Runners.json").write_bytes(Registry)
    Receipt.unlink()
    assert (
        AdvanceCycle(Dispatch, Harness, Receipt, "resume")["status"]
        == "waiting_for_phase_b_claim"
    )
