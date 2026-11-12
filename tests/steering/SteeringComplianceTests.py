from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

from tools.steering.SteeringCompliance import CheckPaths

# command tests need the checked in entry point because fixtures use temporary directories
KCheckerPath = (
    FilePath(__file__).resolve().parents[2]
    / "tools"
    / "steering"
    / "SteeringCompliance.py"
)

# static test methods need standard assertion behavior without violating receiver naming policy
KAssertions = Unittest.TestCase()


# isolated writes prevent leakage because compliance cases require independent fixture state
def WriteSample(FolderPath: FilePath, SourceText: str) -> FilePath:
    SourcePath = FolderPath / "sample.py"
    _ = SourcePath.write_text(SourceText, encoding="utf-8")
    return SourcePath


# subprocess coverage exists because command status codes matter only at the process boundary
class TestCommand(Unittest.TestCase):

    # distinct outcomes exist because automation must separate violations from invalid user input
    @staticmethod
    def CheckCommand() -> None:
        CaseSelf = KAssertions
        BodyText = """# stable values exist because this fixture needs valid module state
KValidValue = 1
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            ValidPath = WriteSample(FolderPath, BodyText)
            ValidResult = Subprocess.run(
                [System.executable, str(KCheckerPath), str(ValidPath)],
                capture_output=True,
                text=True,
                check=False,
            )
            InvalidPath = FolderPath / "missing.py"
            InvalidResult = Subprocess.run(
                [System.executable, str(KCheckerPath), str(InvalidPath)],
                capture_output=True,
                text=True,
                check=False,
            )
        CaseSelf.assertEqual(
            ValidResult.returncode, 0, ValidResult.stdout + ValidResult.stderr
        )
        CaseSelf.assertEqual(InvalidResult.returncode, 2)


# self checking prevents regressions because enforcement sources must follow their own rules
class TestBootstrap(Unittest.TestCase):

    # checker sources pass themselves because enforcement credibility depends on consistent application
    @staticmethod
    def CheckBootstrap() -> None:
        CaseSelf = KAssertions
        TestFilePath = FilePath(__file__).resolve()
        FindingList = CheckPaths([KCheckerPath, TestFilePath])
        CaseSelf.assertEqual(
            FindingList, [], "\n".join(str(FindingInfo) for FindingInfo in FindingList)
        )
