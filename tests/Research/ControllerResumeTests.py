import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckJobResume() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        SourceFile = RootPath / "Source.json"
        _ = SourceFile.write_text('{"dimension":10}', encoding="utf-8")
        _ = Client.RunCli("bind", "source:box", str(SourceFile))
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "parent",
                    "kind": "fixture.inspect",
                    "inputs": {"source": "source:box"},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "child",
                    "kind": "fixture.compare",
                    "inputs": {},
                    "depends_on": ["parent"],
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        for JobName in ("parent", "child"):
            LeaseFile = RootPath / (JobName + ".json")
            Claimed = JsonCodec.loads(
                Client.RunCli(
                    "claim", "--worker", "worker:first", "--claim-file", str(LeaseFile)
                )
            )
            assert Claimed["job"] == JobName
            _ = Client.RunCli(
                "finish",
                "--lease",
                str(LeaseFile),
                "--result",
                str(SourceFile),
                "--outcome",
                "completed",
                "--reason",
                "fixture observation",
            )
        Before = JsonCodec.loads(Client.RunCli("status"))
        assert all(JobInfo["state"] == "completed" for JobInfo in Before["jobs"])
        _ = Client.RunCli("submit", str(JobFile))
        assert JsonCodec.loads(Client.RunCli("status")) == Before
        _ = Client.RunCli("bind", "source:box", str(SourceFile))
        assert JsonCodec.loads(Client.RunCli("status")) == Before
        _ = SourceFile.write_text('{"dimension":12}', encoding="utf-8")
        _ = Client.RunCli("bind", "source:box", str(SourceFile))
        After = JsonCodec.loads(Client.RunCli("status"))
        assert {JobInfo["id"]: JobInfo["state"] for JobInfo in After["jobs"]} == {
            "parent": "queued",
            "child": "waiting_evidence",
        }
        assert all(JobInfo["receipt"] is None for JobInfo in After["jobs"])
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(RootPath / "parent.json"),
            "--result",
            str(SourceFile),
            "--outcome",
            "completed",
            "--reason",
            "stale result",
            ExitCode=1,
        )
