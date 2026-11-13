import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckResources() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        for JobName in ("application:first", "application:second", "offline"):
            _ = JobFile.write_text(
                JsonCodec.dumps(
                    {
                        "id": JobName,
                        "kind": "fixture.inspect",
                        "inputs": {},
                        "rule_version": "rule@1",
                        "tool_version": "tool@1",
                        "resources": (
                            [] if JobName == "offline" else ["application:fixture"]
                        ),
                    }
                ),
                encoding="utf-8",
            )
            _ = Client.RunCli("submit", str(JobFile))
        Offline = RootPath / "Offline.json"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim", "--worker", "worker:offline", "--claim-file", str(Offline)
                )
            )["job"]
            == "offline"
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(Offline),
            "--result",
            str(JobFile),
            "--outcome",
            "completed",
            "--reason",
            "offline fixture",
        )
        _ = Client.RunCli("resource", "application:fixture", "--available")
        FirstFile = RootPath / "First.json"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim", "--worker", "worker:first", "--claim-file", str(FirstFile)
                )
            )["job"]
            == "application:first"
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
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(FirstFile),
            "--result",
            str(JobFile),
            "--outcome",
            "waiting_application",
            "--reason",
            "unhealthy fixture control",
        )
        _ = Client.RunCli("resource", "application:fixture", "--unavailable")
        _ = Client.RunCli("resource", "application:fixture", "--available")
        LeaseFile = RootPath / "Recovered.json"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:recovered",
                    "--claim-file",
                    str(LeaseFile),
                )
            )["job"]
            == "application:first"
        )
