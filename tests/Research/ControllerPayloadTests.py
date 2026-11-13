import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckLargeLease() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        Payload = RootPath / "Large.bin"
        with Payload.open("wb") as Output:
            _ = Output.seek(64 * 1024 * 1024 - 1)
            _ = Output.write(b"x")
        Bound = JsonCodec.loads(Client.RunCli("bind", "large:source", str(Payload)))
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "large",
                    "kind": "fixture.inspect",
                    "inputs": {"source": "large:source"},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        LeaseFile = RootPath / "Lease.json"
        _ = Client.RunCli(
            "claim", "--worker", "worker:large", "--claim-file", str(LeaseFile)
        )
        for _ in range(3):
            BeatInfo = JsonCodec.loads(
                Client.RunCli("heartbeat", "--lease", str(LeaseFile))
            )
            assert BeatInfo["artifact_bytes_hashed"] == 0
            assert BeatInfo["reconciled_jobs"] == 0
            assert BeatInfo["lease_until"] <= BeatInfo["deadline"]
        Artifact = JsonCodec.loads(Client.RunCli("artifact", Bound["sha256"]))
        _ = FilePath(Artifact["path"]).write_bytes(b"corrupt")
        ResultFile = RootPath / "Result.json"
        _ = ResultFile.write_text('{"accepted":true}', encoding="utf-8")
        _ = Client.RunCli(
            "finish",
            "--lease",
            str(LeaseFile),
            "--result",
            str(ResultFile),
            "--outcome",
            "completed",
            "--reason",
            "candidate",
            ExitCode=1,
        )
