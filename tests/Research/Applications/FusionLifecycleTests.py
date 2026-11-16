import json as JsonCodec
import subprocess as Subprocess
import sys as System
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
from tests.Research.SupervisorClient import SessionHost

# the disposable provider hosts the actual owner cli in a separate process
KLifecycleTool = (
    KRepoRoot / "re/automation/ApplicationWorkers/FusionLifecycleFixture.py"
)


# the driver must recover the actual durable paired queue after accepted phase a
def PrepareCycle(Dispatch: DispatchHost) -> tuple[SessionHost, FilePath, bytes]:
    Output = Dispatch.RootPath / "Prepared"
    PlanInfo = PreparePair(Output, False)
    Harness = MakeQueueHost(Dispatch.RootPath, PlanInfo["source_revision"])
    Install = JsonCodec.loads(Dispatch.ConfigFile.read_bytes())
    Install.update(endpoint=str(Dispatch.Endpoint), macos_automatic_quit=True)
    _ = Dispatch.ConfigFile.write_text(JsonCodec.dumps(Install), encoding="utf-8")
    Inbox = Dispatch.RootPath / "Inbox"
    Inbox.mkdir(mode=0o700)
    Receipt = Inbox / "Queue.json"
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
        ],
    )
    Registry = (Dispatch.RootPath / "Runners.json").read_bytes()
    SelectFixture(Dispatch, Harness)
    return Harness, Receipt, Registry


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
            FinishCycle(Dispatch, Harness, Receipt, PhaseB, Claim, Child.pid)
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
) -> None:
    Result = Dispatch.RootPath / "PhaseBResult.json"
    _ = Result.write_text('{"fixture": true}', encoding="utf-8")
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
    _ = AdvanceCycle(Dispatch, Harness, Receipt, "final-lost", 73, PeerPid)
    Active = Dispatch.Endpoint / "fusion-lifecycle-active.json"
    assert Active.is_file()
    Status = AdvanceCycle(Dispatch, Harness, Receipt, "resume")
    assert Status["status"] == "lifecycle_verified"
    PhaseInfo = CastValue(dict[str, object], Status["phase_b"])
    PeerInfo = CastValue(dict[str, object], PhaseInfo["peer"])
    assert PhaseInfo["phase_b_receipt_sha256"] == Harness.ReadJob(PhaseB)["receipt"]
    assert PeerInfo["pid"] == PeerPid
    assert PhaseInfo["native_qualified"] is False
    assert not Active.exists()
