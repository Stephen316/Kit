import json as JsonCodec
import sqlite3 as SqlCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import KRepoRoot, SessionHost


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
    with SqlCodec.connect(DatabasePath) as Database:
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
    for RoleName in (
        "phase-a.receipt",
        "phase-a.measurements",
        "phase-a.P01",
        "phase-a.P04",
    ):
        Expected[RoleName] = {"dependency": PhaseA["id"], "artifact": RoleName}
    assert PhaseB["inputs"] == Expected
    assert PhaseA["resources"] == PhaseB["resources"] == ["application:fusion:local"]


# repeated submission preserves one exact pair and rejects incorrect control provenance
def CheckFusionPair(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Prepared"
    PlanReceipt = JsonCodec.loads(
        RunFusionTool(
            "re/automation/PairedCaptures/FusionFreshProcess.py",
            [
                "--output",
                str(OutputPath),
                "--recipe",
                "P01",
                "--recipe",
                "P04",
                "--read-existing",
            ],
        )
    )
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
    assert not (TmpPath / "AbsentEndpoint").exists()
