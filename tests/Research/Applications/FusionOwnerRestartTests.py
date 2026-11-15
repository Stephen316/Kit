import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.Applications.FusionPhaseQueueTests import (
    MakeQueueHost,
    PreparePair,
    RunFusionTool,
)
from tests.Research.Applications.RunQueueHost import RunQueueHost
from tests.Research.SupervisorClient import SessionHost


# the ordinary queue command supplies definitions and plan bytes before the disposable runner is selected
def PrepareOwner(
    Dispatch: DispatchHost,
) -> tuple[SessionHost, list[str], str]:
    RootPath = Dispatch.RootPath
    OutputPath = RootPath / "Prepared"
    PlanInfo = PreparePair(OutputPath, False)
    Harness = MakeQueueHost(RootPath, PlanInfo["source_revision"])
    InstallInfo = JsonCodec.loads(Dispatch.ConfigFile.read_bytes())
    InstallInfo["endpoint"] = str(Dispatch.Endpoint)
    _ = Dispatch.ConfigFile.write_text(JsonCodec.dumps(InstallInfo), encoding="utf-8")
    QueueText = RunFusionTool(
        "re/automation/ApplicationWorkers/QueueFusionPhases.py",
        [
            "--config",
            str(Harness.ConfigFile),
            "--plan",
            str(OutputPath / "plan.json"),
            "--resource",
            "application:fusion:local",
        ],
    )
    QueuePath = RootPath / "QueueReceipt.json"
    _ = QueuePath.write_text(QueueText, encoding="utf-8")
    PhaseName = CastValue(str, JsonCodec.loads(QueueText)["jobs"]["a"])
    SelectFixture(Dispatch, Harness)
    Arguments = [
        "--installation",
        str(Dispatch.ConfigFile),
        "--store",
        str(Harness.StorePath),
    ]
    return Harness, Arguments + ["--queue-receipt", str(QueuePath)], PhaseName


# manual acknowledgement preserves the completed attempt with its spool until the test releases it
def SelectFixture(Dispatch: DispatchHost, Harness: SessionHost) -> None:
    RegistryPath = Dispatch.RootPath / "Runners.json"
    RegistryInfo = JsonCodec.loads(RegistryPath.read_bytes())
    RunnerInfo = RegistryInfo["runners"]["capture.fusion"]
    del RunnerInfo["application_installation"]
    RunnerInfo["argv"] = Dispatch.Command + [
        "supervised",
        "--installation",
        str(Dispatch.ConfigFile),
        "--session",
        "{session}",
    ]
    _ = RegistryPath.write_text(JsonCodec.dumps(RegistryInfo), encoding="utf-8")
    Terminal = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(Harness.StorePath),
            "resource",
            "application:fusion:local",
            "--capacity",
            "1",
            "--available",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    assert Terminal.returncode == 0, Terminal.stderr


# the executable must explain why it refuses evidence while leaving the retained queue record available
def InvokeRestart(Arguments: list[str], Failure: str = "") -> dict[str, object]:
    ScriptPath = KRepoRoot / "re/automation/ApplicationWorkers/FusionOwnerRestart.py"
    Terminal = Subprocess.run(
        [System.executable, str(ScriptPath), *Arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if Failure:
        assert Terminal.returncode == 1, Terminal.stderr + Terminal.stdout
        assert Failure in Terminal.stderr
        return {}
    assert Terminal.returncode == 0, Terminal.stderr
    return CastValue(dict[str, object], JsonCodec.loads(Terminal.stdout))


# the exact accepted attempt and living owner must persist through registration and a passive recheck
def CheckIntent(TmpPath: FilePath) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Harness, Arguments, PhaseName = PrepareOwner(Dispatch)
    with RunQueueHost(Dispatch, "owner-restart-host") as OldOwner:
        _ = Harness.RunIdle()
        JobInfo = Harness.ReadJob(PhaseName)
        assert JobInfo["state"] == "completed"
        _ = InvokeRestart(Arguments, "spool is still retained")
        AckText = RunFusionTool(
            "re/automation/ApplicationWorkers/AcknowledgeApplication.py",
            Arguments[:-2] + ["--job", PhaseName],
        )
        assert JsonCodec.loads(AckText)["restart_retained"] is True
        VerifyRetained(Dispatch, Arguments, JobInfo, OldOwner)
    _ = InvokeRestart(Arguments + ["--check"], "prior Fusion process is no longer live")


# passive verification must leave each retained byte stable and refuse a changed fence or intent
def VerifyRetained(
    Dispatch: DispatchHost,
    Arguments: list[str],
    JobInfo: dict[str, object],
    OldOwner: dict[str, object],
) -> None:
    JournalPath = Dispatch.Endpoint / "acceptance-journal.json"
    _ = JournalPath.write_bytes(b"{}")
    _ = InvokeRestart(Arguments, "acknowledgement is still pending")
    JournalPath.unlink()
    _ = InvokeRestart(Arguments + ["--check"], "FileNotFoundError")
    assert not list(Dispatch.Endpoint.glob("restart-intent-*.json"))
    Created = InvokeRestart(Arguments)
    IntentPath = FilePath(CastValue(str, Created["intent"]))
    IntentBody = IntentPath.read_bytes()
    IntentInfo = JsonCodec.loads(IntentBody)
    assert IntentInfo["receipt_sha256"] == JobInfo["receipt"]
    assert IntentInfo["result_sha256"] == JobInfo["result"]
    assert IntentInfo["restart_handoff"]["host"] == OldOwner
    assert InvokeRestart(Arguments) == Created
    Verified = InvokeRestart(Arguments + ["--check"])
    assert Verified == {**Created, "status": "intent_verified"}
    assert Verified["native_lifecycle_performed"] is False
    assert IntentPath.read_bytes() == IntentBody
    ExerciseTamper(Dispatch, Arguments, IntentPath, IntentBody)


# altered evidence must be refused even if the handoff still names a live process
def ExerciseTamper(
    Dispatch: DispatchHost,
    Arguments: list[str],
    IntentPath: FilePath,
    IntentBody: bytes,
) -> None:
    FencePath = Dispatch.Endpoint / "fence.json"
    FenceBody = FencePath.read_bytes()
    _ = FencePath.write_bytes(b"{}")
    _ = InvokeRestart(Arguments + ["--check"], "fence differs from accepted phase A")
    assert FencePath.read_bytes() == b"{}"
    _ = FencePath.write_bytes(FenceBody)
    _ = IntentPath.write_bytes(b"{}")
    _ = InvokeRestart(Arguments, "intent differs from current evidence")
    assert IntentPath.read_bytes() == b"{}"
    _ = IntentPath.write_bytes(IntentBody)
