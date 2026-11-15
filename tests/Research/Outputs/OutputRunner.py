import hashlib as Hashing
import json as JsonCodec
import sys as System
from pathlib import Path as FilePath

from tests.Research.Outputs.PrepareOutput import PrepareOutput


def RunOutputs() -> None:
    SessionPath = FilePath(System.argv[1])
    JobInfo = JsonCodec.loads((SessionPath / "job.json").read_text(encoding="utf-8"))
    ModeValue = JobInfo["job"]["options"].get("mode", "complete")
    Content = b"durable editable evidence candidate\x00\xff"
    RelativePath = PrepareOutput(SessionPath, str(ModeValue), Content)
    Artifact = {
        "path": RelativePath,
        "sha256": Hashing.sha256(Content).hexdigest(),
        "size_bytes": len(Content),
    }
    if ModeValue == "digest":
        Artifact["sha256"] = "0" * 64
    elif ModeValue == "size":
        Artifact["size_bytes"] = len(Content) - 1
    Artifacts = {"native": Artifact}
    if ModeValue == "duplicate":
        Artifacts["copy"] = Artifact
    ResultInfo: dict[str, object] = {
        "outcome": "rejected" if ModeValue == "rejected" else "completed",
        "reason": "output fixture finished",
        "records": {"count": 1, "inputs": [], "tokenless": True},
        "artifacts": Artifacts,
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    RunOutputs()
