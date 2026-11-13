import json as JsonCodec
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckAppExpiry() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "application",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                    "resources": ["application:fixture"],
                    "lease_seconds": 1,
                    "timeout_seconds": 2,
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        _ = Client.RunCli("resource", "application:fixture", "--available")
        FirstFile = RootPath / "First.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:lost", "--claim-file", str(FirstFile)
        )
        TimeClock.sleep(1.1)
        assert (
            JsonCodec.loads(Client.RunCli("status"))["jobs"][0]["state"]
            == "waiting_application"
        )
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:blocked",
                    "--claim-file",
                    str(RootPath / "Blocked.json"),
                )
            )["job"]
            is None
        )
        _ = Client.RunCli("resource", "application:fixture", "--available")
        TimeClock.sleep(1.1)
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:recovered",
                    "--claim-file",
                    str(RootPath / "Recovered.json"),
                )
            )["attempt"]
            == 2
        )
        _ = Client.RunCli("heartbeat", "--lease", str(FirstFile), ExitCode=1)
