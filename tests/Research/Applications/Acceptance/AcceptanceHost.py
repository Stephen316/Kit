import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

from tests.Research.Applications.DispatchHost import DispatchHost, KRepoRoot
from tests.Research.SupervisorClient import FixtureJob, SessionHost


# acknowledgement cases need controller acceptance from a real supervisor and application exchange
class AcceptanceHost:

    # a dedicated result schema prevents fixture output from bypassing normal supervisor intake
    def __init__(self, RootPath: FilePath, ModeValue: str = "echo") -> None:
        super().__init__()
        self.Dispatch = DispatchHost(RootPath)
        self.Supervisor = SessionHost(
            RootPath, {"application": 1}, {"fixture.capture": "application"}
        )
        self.JobName = "fixture:application"
        self.ModeValue = ModeValue
        RegistryPath = RootPath / "Runners.json"
        Registry = JsonCodec.loads(RegistryPath.read_text(encoding="utf-8"))
        Registry["runners"]["fixture.capture"].update(
            {
                "argv": self.Dispatch.Command
                + [
                    "supervised",
                    "--installation",
                    str(self.Dispatch.ConfigFile),
                    "--session",
                    "{session}",
                ],
                "result_schema": str(
                    KRepoRoot
                    / "re/automation/ApplicationWorkers/ApplicationResult.json"
                ),
            }
        )
        _ = RegistryPath.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
        self.Supervisor.BindBytes("source", b"fixture inputs")

    # a completed controller attempt must outlive the supervisor process before reconciliation
    def Accept(self) -> FilePath:
        self.Supervisor.SubmitJobs(
            [
                FixtureJob(
                    self.JobName,
                    "fixture.capture",
                    inputs={"source": "source"},
                    options={"mode": self.ModeValue},
                    lease_seconds=30,
                ),
            ]
        )
        _ = self.Supervisor.RunIdle()
        assert self.Supervisor.ReadJob(self.JobName)["state"] == "completed"
        (Spool,) = (self.Dispatch.Endpoint / "jobs").iterdir()
        return Spool

    # the owner command must query the real controller rather than accepting a supplied receipt
    def Reconcile(self, ExitCode: int = 0) -> dict[str, object]:
        Result = Subprocess.run(
            [
                System.executable,
                str(
                    KRepoRoot
                    / "re/automation/ApplicationWorkers/AcknowledgeApplication.py"
                ),
                "--installation",
                str(self.Dispatch.ConfigFile),
                "--store",
                str(self.Supervisor.StorePath),
                "--job",
                self.JobName,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=45,
        )
        assert Result.returncode == ExitCode, Result.stderr + Result.stdout
        if ExitCode:
            assert "application acknowledgement refused" in Result.stderr
            return {}
        Response: dict[str, object] = JsonCodec.loads(Result.stdout)
        return Response
