from __future__ import annotations

import os as OsLib
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[2]

KAssertions = Unittest.TestCase()

KTableText = """KMethodProgram = (
    (0, 4, 1, "primitive:int", 7),
    (4, 8, 2, "primitive:double", float.fromhex("0x1.0p-1")),
)
"""

KProgramText = "EncodedData = ReplayResolved((), 0)\n"

KCleanText = "KPoint = (0, 4)\nKName = ('a', 'b', 'c', 'Feature')\n"


def WriteSource(FolderPath: FilePath, FileName: str, SourceText: str) -> None:
    SourcePath = FolderPath / "src" / "family" / FileName
    SourcePath.parent.mkdir(parents=True, exist_ok=True)
    _ = SourcePath.write_text(SourceText, encoding="utf-8")


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


class TestClean(Unittest.TestCase):

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


class TestRecorded(Unittest.TestCase):

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


class TestInputs(Unittest.TestCase):

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
