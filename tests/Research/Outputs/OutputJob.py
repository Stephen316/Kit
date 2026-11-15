import hashlib as Hashing
import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


# controller artifact checks need a real private job and working directory fixture
class OutputJob(JobClient):

    # each output scenario must start from an isolated lease and staged evidence bytes
    def __init__(self, RootPath: FilePath) -> None:
        super().__init__(RootPath)
        self.RootPath = RootPath
        self.WorkPath = RootPath / "work"
        self.WorkPath.mkdir()
        self.Content = b"declared output payload"
        _ = (self.WorkPath / "native.bin").write_bytes(self.Content)
        self.Artifact = {
            "path": "native.bin",
            "sha256": Hashing.sha256(self.Content).hexdigest(),
            "size_bytes": len(self.Content),
        }
        InputFile = RootPath / "Input.bin"
        _ = InputFile.write_bytes(b"input before")
        _ = self.RunCli("bind", "source", str(InputFile))
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "outputs",
                    "kind": "fixture.outputs",
                    "inputs": {"source": "source"},
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                    "lease_seconds": 300,
                }
            ),
            encoding="utf-8",
        )
        _ = self.RunCli("submit", str(JobFile))
        self.LeaseFile = RootPath / "Lease.json"
        _ = self.RunCli(
            "claim", "--worker", "output:fixture", "--claim-file", str(self.LeaseFile)
        )

    # the fixture must exercise artifact publication through the controller command boundary
    def FinishOutputs(
        self, Manifest: dict[str, object], Outcome: str = "completed", ExitCode: int = 4
    ) -> None:
        FinishFile = self.RootPath / "finish.json"
        _ = FinishFile.write_text(
            JsonCodec.dumps(
                {
                    "session_version": 1,
                    "result": {"outcome": Outcome, "artifacts": Manifest},
                }
            ),
            encoding="utf-8",
        )
        _ = self.RunCli(
            "finish",
            "--lease",
            str(self.LeaseFile),
            "--result",
            str(FinishFile),
            "--outcome",
            Outcome,
            "--reason",
            "output fixture",
            "--output-root",
            str(self.WorkPath),
            ExitCode=ExitCode,
        )
