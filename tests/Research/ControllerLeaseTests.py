import json as JsonCodec
import tempfile as TempFiles
import time as TimeClock
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckLeases() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "interrupted",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                    "max_attempts": 2,
                    "lease_seconds": 1,
                    "timeout_seconds": 2,
                    "retry_base_seconds": 2,
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        FirstFile = RootPath / "First.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:lost", "--claim-file", str(FirstFile)
        )
        Heartbeat = JsonCodec.loads(
            Client.RunCli("heartbeat", "--lease", str(FirstFile))
        )
        assert Heartbeat["lease_until"] <= Heartbeat["deadline"]
        TimeClock.sleep(1.1)
        assert JsonCodec.loads(Client.RunCli("status"))["jobs"][0]["state"] == "queued"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:early",
                    "--claim-file",
                    str(RootPath / "Early.json"),
                )
            )["job"]
            is None
        )
        TimeClock.sleep(2.1)
        SecondFile = RootPath / "Second.json"
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:replacement",
                    "--claim-file",
                    str(SecondFile),
                )
            )["attempt"]
            == 2
        )
        _ = Client.RunCli("heartbeat", "--lease", str(FirstFile), ExitCode=1)
        TimeClock.sleep(1.1)
        Finished = JsonCodec.loads(Client.RunCli("status"))["jobs"][0]
        assert Finished["state"] == "failed"
        assert Finished["attempts"] == 2
        assert Finished["receipt"] is not None
        assert (
            JsonCodec.loads(
                Client.RunCli(
                    "claim",
                    "--worker",
                    "worker:bounded",
                    "--claim-file",
                    str(RootPath / "Bounded.json"),
                )
            )["job"]
            is None
        )
