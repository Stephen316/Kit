import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.JobClient import JobClient


def CheckStoreGuard() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath)
        Client = JobClient(RootPath)
        SourceFile = RootPath / "Source.json"
        _ = SourceFile.write_text('{"dimension":10}', encoding="utf-8")
        Pinned = JsonCodec.loads(Client.RunCli("bind", "source:box", str(SourceFile)))
        JobFile = RootPath / "Job.json"
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "first",
                    "kind": "fixture.inspect",
                    "inputs": {"source": "source:box"},
                    "depends_on": ["second"],
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile))
        PriorFiles = {
            ObjectPath
            for ObjectPath in (RootPath / "State/objects").rglob("*")
            if ObjectPath.is_file()
        }
        _ = JobFile.write_text(
            JsonCodec.dumps(
                {
                    "id": "second",
                    "kind": "fixture.inspect",
                    "inputs": {},
                    "depends_on": ["first"],
                    "rule_version": "rule@1",
                    "tool_version": "tool@1",
                }
            ),
            encoding="utf-8",
        )
        _ = Client.RunCli("submit", str(JobFile), ExitCode=1)
        assert {
            ObjectPath
            for ObjectPath in (RootPath / "State/objects").rglob("*")
            if ObjectPath.is_file()
        } > PriorFiles
        _ = Client.RunCli("bind", "bad';DROP-TABLE-jobs", str(SourceFile), ExitCode=1)
        assert len(JsonCodec.loads(Client.RunCli("status"))["jobs"]) == 1
        Artifact = JsonCodec.loads(Client.RunCli("artifact", Pinned["sha256"]))
        ObjectFile = FilePath(Artifact["path"])
        _ = ObjectFile.write_bytes(b"corrupted")
        _ = Client.RunCli("artifact", Pinned["sha256"], ExitCode=1)
        _ = Client.RunCli("bind", "source:box", str(SourceFile), ExitCode=1)
        _ = Client.RunCli("status", ExitCode=1)
        assert ObjectFile.read_bytes() == b"corrupted"
