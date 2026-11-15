import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Outputs.OutputJob import OutputJob


def CheckBounds() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Client = OutputJob(RootPath)
        Artifact = dict(Client.Artifact)
        Cases: list[dict[str, object]] = [
            {str(Index): dict(Artifact) for Index in range(65)},
            {
                "a": {**Artifact, "size_bytes": 256 * 1024 * 1024},
                "b": {**Artifact, "size_bytes": 1},
            },
            {"a": {**Artifact, "size_bytes": True}},
            {"a": {**Artifact, "size_bytes": -1}},
            {"a": {**Artifact, "path": "/native.bin"}},
            {"a": {**Artifact, "path": "C:/native.bin"}},
            {"a": {**Artifact, "path": "native.bin:alternate"}},
            {"a": {**Artifact, "path": "CON"}},
            {"a": {**Artifact, "path": "missing.bin"}},
            {"a": {**Artifact, "sha256": "A" * 64}},
        ]
        for Manifest in Cases:
            Client.FinishOutputs(Manifest)
            JobInfo = JsonCodec.loads(Client.RunCli("status"))["jobs"][0]
            assert JobInfo["state"] == "running", JobInfo
            assert JobInfo["result"] is None
            assert JobInfo["receipt"] is None
        Client.FinishOutputs({"native": Artifact}, Outcome="retry")
        Digest = str(Artifact["sha256"])
        assert not (RootPath / "State/objects" / Digest[:2] / Digest).exists()


def CheckStale() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Client = OutputJob(RootPath)
        InputFile = RootPath / "Input.bin"
        _ = InputFile.write_bytes(b"changed input")
        _ = Client.RunCli("bind", "source", str(InputFile))
        Client.FinishOutputs({"native": dict(Client.Artifact)}, ExitCode=3)
        JobInfo = JsonCodec.loads(Client.RunCli("status"))["jobs"][0]
        assert JobInfo["state"] == "queued", JobInfo
        assert JobInfo["result"] is None
        assert JobInfo["receipt"] is None
        Digest = str(Client.Artifact["sha256"])
        assert not (RootPath / "State/objects" / Digest[:2] / Digest).exists()
