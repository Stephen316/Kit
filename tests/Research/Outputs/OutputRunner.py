import hashlib as Hashing
import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


def RunOutputs() -> None:
    SessionPath = FilePath(System.argv[1])
    JobInfo = JsonCodec.loads((SessionPath / "job.json").read_text(encoding="utf-8"))
    Mode = JobInfo["job"]["options"].get("mode", "complete")
    Content = b"durable editable evidence candidate\x00\xff"
    WorkPath = SessionPath / "work"
    OutputPath = WorkPath / "native.bin"
    _ = OutputPath.write_bytes(Content)
    RelativePath = "native.bin"
    if Mode == "link":
        OutputPath.unlink()
        OutsidePath = SessionPath / "outside.bin"
        _ = OutsidePath.write_bytes(Content)
        if System.platform == "win32":
            _ = OsLayer.link(OutsidePath, OutputPath)
        else:
            OutputPath.symlink_to(OutsidePath)
    elif Mode == "ancestor":
        OutsidePath = SessionPath / "outside"
        OutsidePath.mkdir()
        _ = (OutsidePath / "native.bin").write_bytes(Content)
        LinkPath = WorkPath / "linked"
        if System.platform == "win32":
            Result = Subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(LinkPath),
                    str(OutsidePath),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            assert Result.returncode == 0, Result.stderr
        else:
            LinkPath.symlink_to(OutsidePath, target_is_directory=True)
        RelativePath = "linked/native.bin"
    elif Mode == "hardlink":
        _ = OsLayer.link(OutputPath, WorkPath / "other.bin")
    elif Mode == "traversal":
        RelativePath = "../work/native.bin"
    Artifact = {
        "path": RelativePath,
        "sha256": Hashing.sha256(Content).hexdigest(),
        "size_bytes": len(Content),
    }
    if Mode == "digest":
        Artifact["sha256"] = "0" * 64
    elif Mode == "size":
        Artifact["size_bytes"] = len(Content) - 1
    Artifacts = {"native": Artifact}
    if Mode == "duplicate":
        Artifacts["copy"] = Artifact
    ResultInfo = {
        "outcome": "rejected" if Mode == "rejected" else "completed",
        "reason": "output fixture finished",
        "records": {"count": 1, "inputs": [], "tokenless": True},
        "artifacts": Artifacts,
    }
    _ = (SessionPath / "result.json").write_text(
        JsonCodec.dumps(ResultInfo), encoding="utf-8"
    )


if __name__ == "__main__":
    RunOutputs()
