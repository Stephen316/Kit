from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture


# git renames must reject invalid ancestors without broadening public package exceptions
def CheckDirRenames() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        FixtureInfo = RepoFixture(FilePath(TmpPath))
        FixtureInfo.WriteFile("src/convert/api/__init__.py")
        FixtureInfo.WriteFile("typings/defusedxml/ElementTree.pyi")
        FixtureInfo.WriteFile("tests/Valid/Alpha.py")
        BaseRef = FixtureInfo.CommitAll("base")
        FixtureInfo.MoveFile("tests/Valid/Alpha.py", "tests/Valid/Bravo.py")
        for FolderName, ExitCode in (("api2", 1), ("ApiCodec", 0)):
            FixtureInfo.WriteFile(f"src/convert/{FolderName}/Bravo.py")
            HeadRef = FixtureInfo.CommitAll(FolderName)
            RunResult = Subprocess.run(
                [
                    System.executable,
                    "-m",
                    "tools.Policy.CheckPaths",
                    "--root",
                    TmpPath,
                    "--base",
                    BaseRef,
                    "--head",
                    HeadRef,
                ],
                cwd=FilePath(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=False,
            )
            assert RunResult.returncode == ExitCode, RunResult.stdout
            assert ("PTH003" in RunResult.stdout) == bool(ExitCode)
            _ = FixtureInfo.RunGit("rm", f"src/convert/{FolderName}/Bravo.py")
