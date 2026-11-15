import os as OsLayer
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


def PrepareOutput(SessionPath: FilePath, ModeValue: str, Content: bytes) -> str:
    WorkPath = SessionPath / "work"
    OutputPath = WorkPath / "native.bin"
    _ = OutputPath.write_bytes(Content)
    RelativePath = "native.bin"
    if ModeValue == "link":
        OutputPath.unlink()
        OutsidePath = SessionPath / "outside.bin"
        _ = OutsidePath.write_bytes(Content)
        if System.platform == "win32":
            OsLayer.link(OutsidePath, OutputPath)
        else:
            OutputPath.symlink_to(OutsidePath)
    elif ModeValue == "ancestor":
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
    elif ModeValue == "hardlink":
        OsLayer.link(OutputPath, WorkPath / "other.bin")
    elif ModeValue == "traversal":
        RelativePath = "../work/native.bin"
    return RelativePath
