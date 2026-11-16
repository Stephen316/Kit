import hashlib as HashLib
import json as JsonCodec
import sqlite3 as SqlCodec
import subprocess as Subprocess
import sys as System
from contextlib import closing as CloseConnection
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as Pytest

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.RunQueueHost import RunQueueHost
from tests.Research.SupervisorClient import KRepoRoot, SessionHost

# the separate scope study uses a closed case roster in both controller jobs
KScope = "two-body-through-all-discovery"


# separate process invocation checks the actual queue and plan command boundaries
def RunFusionTool(ScriptPath: str, Arguments: list[str], ExitCode: int = 0) -> str:
    ResultInfo = Subprocess.run(
        [System.executable, str(KRepoRoot / ScriptPath), *Arguments],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == ExitCode, ResultInfo.stderr
    return ResultInfo.stdout


# a declared capacity does not mark an unavailable native installation ready
def MakeQueueHost(RootPath: FilePath, Revision: str) -> SessionHost:
    Harness = SessionHost(RootPath, {"fusion": 1}, {"capture.fusion": "fusion"})
    InstallPath = RootPath / "Installation.json"
    _ = InstallPath.write_text(
        JsonCodec.dumps(
            {
                "version": 1,
                "installation": "fusion:local",
                "application": "fusion",
                "endpoint": str(RootPath / "AbsentEndpoint"),
                "source_root": str(KRepoRoot),
                "source_revision": Revision,
            }
        ),
        encoding="utf-8",
    )
    WorkerRoot = KRepoRoot / "re/automation/ApplicationWorkers"
    RegistryPath = RootPath / "Runners.json"
    Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
    Registry["runners"]["capture.fusion"].update(
        {
            "argv": [
                System.executable,
                str(WorkerRoot / "FusionApplicationWorker.py"),
                "--installation",
                str(InstallPath),
                "{session}",
            ],
            "result_schema": str(WorkerRoot / "ApplicationResult.json"),
            "application_installation": str(InstallPath),
        }
    )
    _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    Config = JsonCodec.loads(Harness.ConfigFile.read_text(encoding="utf-8"))
    Config["resources"] = {"application:fusion:local": 1}
    _ = Harness.ConfigFile.write_text(JsonCodec.dumps(Config), encoding="utf-8")
    return Harness


# the actual queued records must bind the accepted dependencies without new global names
def VerifyPhaseJobs(Harness: SessionHost, Receipt: dict[str, object]) -> None:
    Names = JsonCodec.loads(JsonCodec.dumps(Receipt["jobs"]))
    Binding = Receipt["plan_binding"]
    assert Harness.ReadJob(Names["a"])["state"] == "waiting_application"
    assert Harness.ReadJob(Names["b"])["state"] == "waiting_evidence"
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    with CloseConnection(SqlCodec.connect(DatabasePath)) as Database:
        assert Database.execute("SELECT name,sha256 FROM bindings").fetchall() == [
            (Binding, Receipt["plan_sha256"])
        ]
        assert Database.execute("SELECT COUNT(*) FROM resources").fetchone() == (0,)
        JobRows = Database.execute("SELECT definition FROM jobs ORDER BY id").fetchall()
    PhaseA, PhaseB = [JsonCodec.loads(RowInfo[0]) for RowInfo in JobRows]
    assert PhaseA["inputs"] == {"plan": Binding}
    assert PhaseB["depends_on"] == [PhaseA["id"]]
    Expected: dict[str, object] = {
        "plan": Binding,
        "phase-a.accepted": {"dependency": PhaseA["id"]},
    }
    for RoleName in ScopeRoles(Receipt, PhaseA, PhaseB):
        Expected[RoleName] = {"dependency": PhaseA["id"], "artifact": RoleName}
    assert PhaseB["inputs"] == Expected
    assert PhaseA["resources"] == PhaseB["resources"] == ["application:fusion:local"]


# the fixed job envelope identifies the scope case set without changing legacy jobs
def ScopeRoles(
    Receipt: dict[str, object],
    PhaseA: dict[str, object],
    PhaseB: dict[str, object],
) -> tuple[str, ...]:
    if Receipt.get("scope") == KScope:
        assert Receipt["cases"] == ["automatic", "explicit_a", "explicit_ab"]
        assert "recipes" not in Receipt
        assert PhaseA["options"] == {"phase": "a", "scope": KScope}
        assert PhaseB["options"] == {"phase": "b", "scope": KScope}
        assert (
            PhaseA["rule_version"]
            == PhaseB["rule_version"]
            == "fusion-through-all-scope@1"
        )
        return (
            "phase-a.receipt",
            "phase-a.report",
            "phase-a.automatic",
            "phase-a.explicit_a",
            "phase-a.explicit_ab",
        )
    assert Receipt["recipes"] == ["P01", "P04"]
    assert PhaseA["options"] == {"phase": "a"}
    assert PhaseB["options"] == {"phase": "b"}
    return "phase-a.receipt", "phase-a.measurements", "phase-a.P01", "phase-a.P04"


# a pending evidence audit must leave the queue and unavailable application resource intact
def VerifyAudit(Harness: SessionHost, Receipt: dict[str, object]) -> None:
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    DigestBefore = HashLib.sha256(DatabasePath.read_bytes()).hexdigest()
    ReceiptPath = Harness.RootPath / "QueueReceipt.json"
    _ = ReceiptPath.write_text(JsonCodec.dumps(Receipt), encoding="utf-8")
    Audit = JsonCodec.loads(
        RunFusionTool(
            "re/automation/ApplicationWorkers/AuditFusionPhases.py",
            ["--store", str(Harness.StorePath), "--queue-receipt", str(ReceiptPath)],
        )
    )
    assert Audit["status"] == "pending"
    assert Audit.get("scope") == Receipt.get("scope")
    assert Audit["launched_application"] is Audit["native_qualified"] is False
    assert Audit["resource_available"] is False
    assert Audit["phases"]["a"]["state"] == "waiting_application"
    assert Audit["phases"]["b"]["state"] == "waiting_evidence"
    assert HashLib.sha256(DatabasePath.read_bytes()).hexdigest() == DigestBefore


# repeated submission preserves one exact pair and rejects incorrect control provenance
@Pytest.mark.parametrize("ScopeRun", (False, True), ids=("discovery", "scope"))
def CheckFusionPair(TmpPath: FilePath, ScopeRun: bool) -> None:
    OutputPath = TmpPath / "Prepared"
    PlanReceipt = PreparePair(OutputPath, ScopeRun)
    Harness = MakeQueueHost(TmpPath, PlanReceipt["source_revision"])
    PlanPath = OutputPath / "plan.json"
    Arguments = [
        "--config",
        str(Harness.ConfigFile),
        "--resource",
        "application:fusion:local",
    ]
    QueuePath = "re/automation/ApplicationWorkers/QueueFusionPhases.py"
    Receipt: dict[str, object] = JsonCodec.loads(
        RunFusionTool(QueuePath, Arguments + ["--plan", str(PlanPath)])
    )
    assert Receipt["supervised_acknowledgement"] is True
    assert Receipt["plan_sha256"] == PlanReceipt["plan_sha256"]
    assert (
        JsonCodec.loads(RunFusionTool(QueuePath, Arguments + ["--plan", str(PlanPath)]))
        == Receipt
    )
    BadPlan = JsonCodec.loads(PlanPath.read_bytes())
    BadPlan["pins"]["control"]["sha256"] = "0" * 64
    BadPath = TmpPath / "TamperedPlan.json"
    _ = BadPath.write_text(JsonCodec.dumps(BadPlan), encoding="utf-8")
    _ = RunFusionTool(QueuePath, Arguments + ["--plan", str(BadPath)], ExitCode=1)
    VerifyPhaseJobs(Harness, Receipt)
    VerifyAudit(Harness, Receipt)
    assert not (TmpPath / "AbsentEndpoint").exists()


# the child runs the actual queue and interrupts only at the selected persistence boundary
def InterruptQueue(QueuePath: str, Arguments: list[str], Checkpoint: str) -> None:
    ScriptText = """
import os
import runpy
import sys
from pathlib import Path

script, checkpoint, *arguments = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
queue = runpy.run_path(script)
scope = queue["main"].__globals__

def interrupt(*args, **kwargs):
    os._exit(73)

if checkpoint == "before-ledger":
    scope["submit_pair"] = interrupt
else:
    seal = scope["seal"]
    receipt = Path(arguments[-1])

    def stop_before_receipt(path, raw):
        if path == receipt:
            interrupt()
        seal(path, raw)

    scope["seal"] = stop_before_receipt
sys.argv = [script, *arguments]
sys.exit(queue["main"]())
"""
    ResultInfo = Subprocess.run(
        [
            System.executable,
            "-c",
            ScriptText,
            str(KRepoRoot / QueuePath),
            Checkpoint,
            *Arguments,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 73, ResultInfo.stderr
    assert ResultInfo.stdout == ""


# a lost receipt must recover the committed pair without another submission or a new plan
@Pytest.mark.skipif(
    System.platform not in ("darwin", "linux"), reason="POSIX receipt custody"
)
def CheckReceipt(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Prepared"
    PlanReceipt = PreparePair(OutputPath, False)
    Harness = MakeQueueHost(TmpPath, PlanReceipt["source_revision"])
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    PrivatePath = TmpPath.resolve() / "private"
    PrivatePath.mkdir(mode=0o700)
    ReceiptPath = PrivatePath / "QueueReceipt.json"
    PlanPath = OutputPath / "plan.json"
    QueuePath = "re/automation/ApplicationWorkers/QueueFusionPhases.py"
    Config = ["--config", str(Harness.ConfigFile)]
    Arguments = Config + [
        "--resource",
        "application:fusion:local",
        "--plan",
        str(PlanPath),
        "--receipt",
        str(ReceiptPath),
    ]
    Recovery = Config + ["--recover-receipt", str(ReceiptPath)]
    InterruptQueue(QueuePath, Arguments, "before-ledger")
    _ = RunFusionTool(QueuePath, Recovery, ExitCode=1)
    assert not ReceiptPath.exists()
    with CloseConnection(SqlCodec.connect(DatabasePath)) as Database:
        assert Database.execute("SELECT COUNT(*) FROM jobs").fetchone() == (0,)

    InterruptQueue(QueuePath, Arguments, "before-receipt")
    assert not ReceiptPath.exists()
    DigestBefore = HashLib.sha256(DatabasePath.read_bytes()).hexdigest()
    _ = RunFusionTool(QueuePath, Arguments + ["--run", "conflict"], ExitCode=1)
    PlanPath.unlink()
    VerifyRecovery(Harness, ReceiptPath, QueuePath, Recovery, DigestBefore)


# repeated read only recovery verifies the same committed definitions and never overwrites a receipt
def VerifyRecovery(
    Harness: SessionHost,
    ReceiptPath: FilePath,
    QueuePath: str,
    Recovery: list[str],
    DigestBefore: str,
) -> None:
    assert Harness.StorePath is not None
    DatabasePath = Harness.StorePath / "ledger.sqlite3"
    Stdout = RunFusionTool(QueuePath, Recovery)
    Receipt: dict[str, object] = JsonCodec.loads(Stdout)
    assert ReceiptPath.read_bytes() == Stdout.encode("utf-8")
    assert ReceiptPath.stat().st_mode & 0o077 == 0
    assert RunFusionTool(QueuePath, Recovery) == Stdout
    assert HashLib.sha256(DatabasePath.read_bytes()).hexdigest() == DigestBefore
    VerifyPhaseJobs(Harness, Receipt)
    VerifyAudit(Harness, Receipt)
    with CloseConnection(SqlCodec.connect(DatabasePath)) as Database:
        assert Database.execute(
            "SELECT COUNT(*) FROM events WHERE action='submitted'"
        ).fetchone() == (2,)
    _ = ReceiptPath.write_text('{"conflict":true}\n', encoding="utf-8")
    _ = RunFusionTool(QueuePath, Recovery, ExitCode=1)
    assert ReceiptPath.read_text(encoding="utf-8") == '{"conflict":true}\n'
    assert not (Harness.RootPath / "AbsentEndpoint").exists()


# preparation binds the actual recipe or scope program without opening the application
def PreparePair(OutputPath: FilePath, ScopeRun: bool) -> dict[str, str]:
    Arguments = ["--output", str(OutputPath)]
    RootPath = "re/automation/PairedCaptures"
    if ScopeRun:
        ScriptPath = f"{RootPath}/ScopeControl/FusionScopeControl.py"
    else:
        ScriptPath = f"{RootPath}/FusionFreshProcess.py"
        Arguments.extend(("--recipe", "P01", "--recipe", "P04", "--read-existing"))
    return CastValue(
        dict[str, str], JsonCodec.loads(RunFusionTool(ScriptPath, Arguments))
    )


# live claim state must come from the exact queue command and worker registry
def QueuePhases(Dispatch: DispatchHost) -> tuple[SessionHost, str, str]:
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
    Names: dict[str, str] = JsonCodec.loads(QueueText)["jobs"]
    return Harness, Names["a"], Names["b"]


# one bad control must discard every recipe result and preserve the owner evidence
@Pytest.mark.skipif(System.platform != "darwin", reason="macOS application worker")
@Pytest.mark.parametrize(
    ("FaultKind", "ReasonText"),
    (
        ("after", "Fusion phase did not preserve both healthy pinned controls"),
        ("fixture", "Fusion fixture reports cannot settle a native phase"),
    ),
)
def CheckControls(TmpPath: FilePath, FaultKind: str, ReasonText: str) -> None:
    Dispatch = DispatchHost(TmpPath.resolve())
    Dispatch.Command = [
        System.executable,
        str(KRepoRoot / "re/automation/ApplicationWorkers/FusionPhaseHealthFixture.py"),
    ]
    Harness, FirstName, RepeatName = QueuePhases(Dispatch)
    with RunQueueHost(Dispatch, FaultKind):
        _ = Harness.RunIdle()
        assert Harness.ReadJob(FirstName)["state"] == "rejected"
        assert Harness.ReadJob(RepeatName)["state"] == "waiting_evidence"
        Finish = Harness.ReadResult(FirstName)
        ResultInfo = JsonCodec.loads(JsonCodec.dumps(Finish["result"]))
        assert ResultInfo["outcome"] == "rejected"
        assert ReasonText in ResultInfo["reason"]
        assert "artifacts" not in ResultInfo and "output_artifacts" not in Finish
        AssertSpool(Dispatch)


# owner disposition must retain the completed files behind their original fence
def AssertSpool(Dispatch: DispatchHost) -> None:
    Fence = JsonCodec.loads((Dispatch.Endpoint / "fence.json").read_bytes())
    assert Fence["reason"] == "acceptance_required"
    Spool = Dispatch.Endpoint / "jobs" / Fence["job_id"]
    assert (Spool / "pending-acceptance.json").is_file()
    Reply = JsonCodec.loads((Spool / "phase.done").read_bytes())
    Copied = JsonCodec.loads((Spool / "copied.json").read_bytes())
    assert Reply["status"] == "completed"
    assert Copied["status"] == "copied_pending_controller_acceptance"
    assert Reply["files"] == Copied["artifacts"]
    for Recipe in ("P01", "P04"):
        assert (Spool / f"phase-a/{Recipe}-fusion-fresh-baseline-a.f3d").is_file()
