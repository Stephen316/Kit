import json as JsonCodec
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.FusionPhaseQueueTests import (
    MakeQueueHost,
    PreparePair,
    RunFusionTool,
)
from tests.Research.SupervisorClient import FixtureJob, SessionHost

# the research fixture runs the owner commands in independent macos processes
KFixtureTool = "re/automation/ApplicationWorkers/FusionColdStartFixture.py"

# the production entry is invoked unchanged when resuming the sealed launch
KOwnerTool = "re/automation/ApplicationWorkers/FusionOwnerColdStart.py"

# normal continuous lifecycle entry also needs to resume the same sealed startup
KLifecycleTool = "re/automation/ApplicationWorkers/FusionLifecycleOwner.py"


# the real queue is populated while the installation resource is still unavailable
def PrepareCold(Dispatch: DispatchHost) -> tuple[SessionHost, list[str], str]:
    Prepared = Dispatch.RootPath / "Prepared"
    PlanInfo = PreparePair(Prepared, False)
    Harness = MakeQueueHost(Dispatch.RootPath, PlanInfo["source_revision"])
    Installation = JsonCodec.loads(Dispatch.ConfigFile.read_bytes())
    Installation.update(endpoint=str(Dispatch.Endpoint), macos_automatic_quit=True)
    _ = Dispatch.ConfigFile.write_text(JsonCodec.dumps(Installation), encoding="utf-8")
    _ = RunFusionTool(
        KFixtureTool, ["stage", str(Dispatch.RootPath), str(Dispatch.ConfigFile)]
    )
    QueueRival(Harness)
    QueuePath = Dispatch.RootPath / "ColdPair.json"
    Queued = RunFusionTool(
        "re/automation/ApplicationWorkers/QueueFusionPhases.py",
        [
            "--config",
            str(Harness.ConfigFile),
            "--plan",
            str(Prepared / "plan.json"),
            "--resource",
            "application:fusion:local",
            "--receipt",
            str(QueuePath),
            "--owner-lifecycle",
        ],
    )
    PhaseName = CastValue(str, JsonCodec.loads(Queued)["jobs"]["a"])
    Flags = ColdFlags(Dispatch, Harness, QueuePath)
    return Harness, Flags, PhaseName


# the older healthy job would win fifo selection if startup opened the whole resource
def QueueRival(Harness: SessionHost) -> None:
    Harness.SubmitJobs(
        [
            FixtureJob(
                "fixture:cold-rival",
                "capture.fusion",
                resources=["application:fusion:local"],
            )
        ]
    )
    _ = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:fusion:local",
            "--capacity",
            "1",
        ],
    )


# both owner invocations must bind the same installation profile and durable queue
def ColdFlags(
    Dispatch: DispatchHost, Harness: SessionHost, QueuePath: FilePath
) -> list[str]:
    return [
        "--config",
        str(Harness.ConfigFile),
        "--installation",
        str(Dispatch.ConfigFile),
        "--lifecycle",
        str(Dispatch.RootPath / "Lifecycle.json"),
        "--profile",
        str(Dispatch.RootPath / "Staged/startup-profile.json"),
        "--queue-receipt",
        str(QueuePath),
        "--launch-seconds",
        "30",
        "--startup-seconds",
        "15",
    ]


# masking the test copy of the provider receipt exercises the ambiguous retry boundary
def AssertNoReply(Dispatch: DispatchHost, Flags: list[str]) -> None:
    Receipt = Dispatch.Endpoint / "cold-start-peer.json"
    Withheld = Receipt.with_suffix(".withheld")
    _ = Receipt.rename(Withheld)
    try:
        Output = RunFusionTool(KOwnerTool, Flags, ExitCode=2)
        assert JsonCodec.loads(Output) == {"status": "cold_launch_unobserved"}
        assert RunInitialOwner(Dispatch, Flags, ExitCode=2) == JsonCodec.loads(Output)
    finally:
        _ = Withheld.rename(Receipt)


# the normal owner cli must make startup progress at the same durable custody boundary
def RunInitialOwner(
    Dispatch: DispatchHost, Flags: list[str], ExitCode: int = 0
) -> dict[str, object]:
    Output = RunFusionTool(
        KLifecycleTool,
        [*Flags, "--queue-directory", str(Dispatch.RootPath), "--once"],
        ExitCode=ExitCode,
    )
    return CastValue(dict[str, object], JsonCodec.loads(Output))


# a single real claim verifies controller availability and exact first admission
def ClaimBoot(Harness: SessionHost, Destination: str) -> object:
    ClaimPath = Harness.RootPath / Destination
    Output = RunFusionTool(
        "re/automation/Controller.py",
        [
            "--store",
            str(Harness.StorePath),
            "claim",
            "--worker",
            "fixture:cold",
            "--claim-file",
            str(ClaimPath),
        ],
    )
    return JsonCodec.loads(Output)["job"]


# an external availability toggle still cannot admit work before startup proof
def AssertDeferred(Harness: SessionHost) -> None:
    Endpoint = [
        "--store",
        str(Harness.StorePath),
        "resource",
        "application:fusion:local",
    ]
    _ = RunFusionTool("re/automation/Controller.py", Endpoint + ["--available"])
    try:
        assert ClaimBoot(Harness, "EarlyClaim.json") is None
    finally:
        _ = RunFusionTool("re/automation/Controller.py", Endpoint + ["--unavailable"])


# interrupted ownership and older contenders cannot cause another bundle launch or claim
@TestMark.skipif(
    System.platform != "darwin", reason="macOS owner cold-start process custody"
)
def CheckColdStart(TmpPath: FilePath) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Flags, PhaseName = PrepareCold(Dispatch)
    assert Harness.ReadJob(PhaseName)["state"] == "waiting_application"
    try:
        _ = RunFusionTool(KFixtureTool, ["interrupt", *Flags], ExitCode=74)
        Request = Dispatch.Endpoint / "cold-start-launch.json"
        Sealed = Request.read_bytes()
        AssertNoReply(Dispatch, Flags)
        AssertDeferred(Harness)
        Claimed = RunInitialOwner(Dispatch, Flags)
        assert Claimed["job"] == PhaseName
        assert Claimed["status"] == "initial_phase_a_admission_recorded"
        assert ClaimBoot(Harness, "SelectedClaim.json") == PhaseName
        assert JsonCodec.loads(RunFusionTool(KOwnerTool, Flags)) == Claimed
        assert Request.read_bytes() == Sealed
        assert not (Dispatch.Endpoint / "fence.json").exists()
    finally:
        _ = RunFusionTool(
            KFixtureTool, ["cleanup", str(Dispatch.RootPath), str(Dispatch.Endpoint)]
        )
