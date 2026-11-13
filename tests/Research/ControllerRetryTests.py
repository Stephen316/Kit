import json as JsonCodec
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckRetryPark() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        SourceFile = RootPath / "Signal.json"
        _ = SourceFile.write_text('{"ci":"pending"}', encoding="utf-8")
        _ = Client.RunCli("bind", "ci:fixture", str(SourceFile))
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "retry",
                    "kind": "fixture.inspect",
                    "inputs": {"ci": "ci:fixture"},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                    "max_attempts": 2,
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        LeaseFile = RootPath / "Waiting.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:waiting", "--claim-file", str(LeaseFile)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeaseFile),
            "--result",
            str(SourceFile),
            "--outcome",
            "waiting_ci",
            "--reason",
            "fixture CI is pending",
        )
        _ = Client.RunCli("bind", "ci:fixture", str(SourceFile))
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:parked",
                    "--claim-file",
                    str(RootPath / "Parked.json"),
                )
            )["job"]
            is None
        )
        _ = SourceFile.write_text('{"ci":"passed"}', encoding="utf-8")
        _ = Client.RunCli("bind", "ci:fixture", str(SourceFile))
        for Index in range(2):
            LeaseFile = RootPath / f"Retry{Index}.json"
            assert (
                JsonCodec.loads(
                    Client.RunCli(
                        "claim",
                        "--worker",
                        "worker:retry",
                        "--claim-file",
                        str(LeaseFile),
                    )
                )["attempt"]
                == Index + 1
            )
            _ = Client.RunCli(
                "finish",
                "--lease",
                str(LeaseFile),
                "--result",
                str(SourceFile),
                "--outcome",
                "retry",
                "--reason",
                "transient fixture failure",
            )
            if Index == 0:
                TimeClock.sleep(1.1)
        assert JsonCodec.loads(Client.RunCli("status"))["jobs"][0]["state"] == "failed"
