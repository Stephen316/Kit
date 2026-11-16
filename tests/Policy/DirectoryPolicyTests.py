from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture


# real command execution protects full tree and revision scans from lowercase directory regressions
def CheckCodeDirs() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        FixtureInfo = RepoFixture(FilePath(TmpPath))
        for RootName in ("src", "tools", "typings", "tests"):
            FixtureInfo.WriteFile(f"{RootName}/bad_name/Alpha.py")
        BaseRef = FixtureInfo.CommitAll("base")
        FixtureInfo.WriteFile("tests/Valid/Bravo.py")
        HeadRef = FixtureInfo.CommitAll("head")
        BaseArgs = [
            System.executable,
            "-m",
            "tools.Policy.CheckPaths",
            "--root",
            TmpPath,
        ]
        for ArgItems in ([], ["--base", BaseRef, "--head", HeadRef]):
            RunResult = Subprocess.run(
                [*BaseArgs, *ArgItems],
                cwd=FilePath(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=False,
            )
            assert RunResult.returncode == (0 if ArgItems else 1), RunResult.stderr
            assert RunResult.stdout.count("PTH003") == (0 if ArgItems else 4)
