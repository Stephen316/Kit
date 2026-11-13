import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckRuleChange() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "versioned",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        OldLease = RootPath / "Old.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:old", "--claim-file", str(OldLease)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(OldLease),
            "--result",
            str(JobFile),
            "--outcome",
            "rejected",
            "--reason",
            "counterexample",
        )
        _ = Client.RunCli("submit", str(JobFile))
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
        Payload = JsonCodec.loads(JobFile.read_text(encoding="utf-8"))
        Payload["rule_version"] = "rule@2"
        _ = JobFile.write_text(JsonCodec.dumps(Payload), encoding="utf-8")
        _ = Client.RunCli("submit", str(JobFile))
        NewLease = RootPath / "New.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:new", "--claim-file", str(NewLease)
        )
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(OldLease),
            "--result",
            str(JobFile),
            "--outcome",
            "completed",
            "--reason",
            "stale worker",
            ExitCode=1,
        )
        assert JsonCodec.loads(Client.RunCli("status"))["jobs"][0]["state"] == "running"
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(NewLease),
            "--result",
            str(JobFile),
            "--outcome",
            "completed",
            "--reason",
            "new scoped rule",
        )
        Completed = JsonCodec.loads(Client.RunCli("status"))["jobs"][0]
        Receipt = JsonCodec.loads(Client.RunCli("artifact", Completed["receipt"]))
        Evidence = JsonCodec.loads(
            FilePath(Receipt["path"]).read_text(encoding="utf-8")
        )
        assert Evidence["rule_version"] == "rule@2"
        assert (
            Evidence["snapshot"]["definition_hash"]
            != JsonCodec.loads(OldLease.read_text())["snapshot"]["definition_hash"]
        )
