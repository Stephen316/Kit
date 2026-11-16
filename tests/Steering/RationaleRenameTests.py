from __future__ import annotations

import tempfile as Tempfile
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture
from tests.Steering.RationaleCommentsTests import KCleanSource
from tests.Steering.RationaleCommentsTests import RunModule


# repository moves must preserve old comments while still rejecting new explanatory additions
def CheckRenameGate() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        FixtureInfo = RepoFixture(RootPath)
        SourceText = KCleanSource + "\n# historical explanation\n"
        FixtureInfo.WriteFile("Alpha.py", SourceText)
        BaseRef = FixtureInfo.CommitAll("base")
        FixtureInfo.MoveFile("Alpha.py", "Bravo.py")
        HeadRef = FixtureInfo.CommitAll("rename")
        PassedInfo = RunModule(RootPath, BaseRef, HeadRef)
        FixtureInfo.WriteFile("Bravo.py", SourceText + "\n# new explanation\n")
        HeadRef = FixtureInfo.CommitAll("add explanation")
        FailedInfo = RunModule(RootPath, BaseRef, HeadRef)
    assert PassedInfo.returncode == 0, PassedInfo.stdout + PassedInfo.stderr
    assert FailedInfo.returncode == 1, FailedInfo.stdout + FailedInfo.stderr
    assert FailedInfo.stdout.count("CMT002") == 1
