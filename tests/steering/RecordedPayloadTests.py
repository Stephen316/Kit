from __future__ import annotations

import os as OsLib
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

# repo root needs a stable location so source policy resolves inputs independently of the caller working directory
KRepoRoot = FilePath(__file__).resolve().parents[2]

# the assertions cases must remain explicit so source policy exercises the intended compatibility boundary
KAssertions = Unittest.TestCase()

# the table text cases must remain explicit so source policy exercises the intended compatibility boundary
KTableText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
)
"""

# the program text cases must remain explicit so source policy exercises the intended compatibility boundary
KProgramText = "EncodedData = ReplayResolved((), 0)\n"

# the clean text cases must remain explicit so source policy exercises the intended compatibility boundary
KCleanText = "KPoint = (0, 4)\nKName = ('a', 'b', 'c', 'Feature')\n"


# shared write source setup keeps fixtures consistent so source policy failures identify the intended compatibility boundary
def WriteSource(FolderPath: FilePath, FileName: str, SourceText: str) -> None:
    SourcePath = FolderPath / "src" / "family" / FileName
    SourcePath.parent.mkdir(parents=True, exist_ok=True)
    _ = SourcePath.write_text(SourceText, encoding="utf-8")


# shared run setup keeps fixtures consistent so source policy failures identify the intended compatibility boundary
def RunCheck(FolderPath: FilePath, *ArgValues: str) -> Subprocess.CompletedProcess[str]:
    EnvValues = {**OsLib.environ, "PYTHONPATH": str(KRepoRoot)}
    return Subprocess.run(
        [System.executable, "-m", "tools.Donors.CheckReplays", *ArgValues],
        capture_output=True,
        text=True,
        check=False,
        cwd=FolderPath,
        env=EnvValues,
    )


# the clean boundary needs grouped coverage so repository automation cannot silently change its observable contract
class TestClean(Unittest.TestCase):

    # the clean contract needs boundary coverage so invalid owned sources fail at the command boundary
    @staticmethod
    def CheckClean() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteSource(FolderPath, "Clean.py", KCleanText)
            ResultInfo = RunCheck(FolderPath, "src")
        CaseSelf.assertEqual(
            ResultInfo.returncode, 0, ResultInfo.stdout + ResultInfo.stderr
        )
        CaseSelf.assertIn("no recorded payloads in 1 files", ResultInfo.stdout)


# the recorded boundary needs grouped coverage so repository automation cannot silently change its observable contract
class TestRecorded(Unittest.TestCase):

    # the recorded contract needs boundary coverage so invalid owned sources fail at the command boundary
    @staticmethod
    def CheckRecorded() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            WriteSource(FolderPath, "Clean.py", KCleanText)
            WriteSource(FolderPath, "Table.py", KTableText)
            WriteSource(FolderPath, "Program.py", KProgramText)
            ResultInfo = RunCheck(FolderPath, "src")
        CaseSelf.assertEqual(ResultInfo.returncode, 1)
        CaseSelf.assertIn(
            "src/family/Table.py: 2 recorded field operations, 0 re-emission calls",
            ResultInfo.stdout,
        )
        CaseSelf.assertIn(
            "src/family/Program.py: 0 recorded field operations, 1 re-emission calls",
            ResultInfo.stdout,
        )
        CaseSelf.assertNotIn("Clean.py", ResultInfo.stdout)
        CaseSelf.assertIn("found in 2 files", ResultInfo.stderr)


# the inputs boundary needs grouped coverage so repository automation cannot silently change its observable contract
class TestInputs(Unittest.TestCase):

    # the inputs contract needs boundary coverage so invalid owned sources fail at the command boundary
    @staticmethod
    def CheckInputs() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            MissingInfo = RunCheck(FolderPath, "src")
            WriteSource(FolderPath, "Broken.py", "KValue = (\n")
            BrokenInfo = RunCheck(FolderPath, "src")
        CaseSelf.assertEqual(MissingInfo.returncode, 2)
        CaseSelf.assertIn("path does not exist", MissingInfo.stderr)
        CaseSelf.assertEqual(BrokenInfo.returncode, 2)
        CaseSelf.assertIn("input error", BrokenInfo.stderr)
