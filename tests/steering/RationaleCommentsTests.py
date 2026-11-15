from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as UnitTest
from pathlib import Path as FilePath

from pytest import mark as TestMarks

from tests.Policy.RepoFixture import RepoFixture

# fixture sources must carry one compliant rationale so clean cases prove real coverage
KCleanSource = """\

# doubling stays shared so fixture comparisons exercise consistent source behavior
def Double(Value):
    return Value * 2
"""

# fixture sources omit the mandatory rationale so violation detection gets exercised
KBadSource = """\
def Broken():
    return 1
"""


# subprocess execution exercises the real entry point including argument handling
def RunModule(
    RootPath: FilePath,
    BaseRef: str | None = None,
    HeadRef: str | None = None,
) -> Subprocess.CompletedProcess[str]:
    WorkPath = FilePath(__file__).resolve().parents[2]
    ArgItems = [
        System.executable,
        "-m",
        "tools.steering.CheckRationaleComments",
        "--root",
        str(RootPath),
    ]
    if BaseRef is not None:
        ArgItems.extend(["--base", BaseRef])
    if HeadRef is not None:
        ArgItems.extend(["--head", HeadRef])
    return Subprocess.run(
        ArgItems,
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
    )


# diff coverage proves the gate fails only for violations a reviewed change deepens
class TestDiffGate(UnitTest.TestCase):

    # diff gates must fail only for violations the reviewed change introduces or deepens
    def CheckDiffGate(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            InvalidSource = KCleanSource.replace("doubling", "Doubling")
            FixtureInfo.WriteFile("Legacy.py", InvalidSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Bravo.py", InvalidSource)
            FixtureInfo.WriteFile("re/Nested.py", InvalidSource)
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 1, ResultInfo.stderr)
        self.assertIn("Bravo.py", ResultInfo.stdout)
        self.assertNotIn("Legacy.py", ResultInfo.stdout)
        self.assertNotIn("Nested.py", ResultInfo.stdout)

    # deleting one mandated rationale must fail the gate even without touching code
    def CheckCommentLoss(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Alpha.py", KBadSource)
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 1, ResultInfo.stderr)
        self.assertIn("RAT001", ResultInfo.stdout)


# scope coverage proves excluded trees and non python edits never trigger failures
class TestScopeGate(UnitTest.TestCase):

    # full tree mode proves tracked exclusions keep vendored debt out of scope
    def CheckFullPass(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            FixtureInfo.WriteFile("re/Nested.py", KBadSource)
            _ = FixtureInfo.CommitAll("base")
            ResultInfo = RunModule(RootPath)
        self.assertEqual(ResultInfo.returncode, 0, ResultInfo.stdout)
        self.assertIn("passed", ResultInfo.stdout)
        self.assertNotIn("Nested", ResultInfo.stdout)

    # non python edits must stay out of scope so documentation work never triggers gates
    def CheckTxtOnly(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.WriteFile("Note.txt", "notes\n")
            HeadRef = FixtureInfo.CommitAll("head")
            ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
        self.assertEqual(ResultInfo.returncode, 0, ResultInfo.stdout)


# argument coverage proves partial revision flags fail fast before any comparison
class TestArgGate(UnitTest.TestCase):

    # partial revision flags must fail fast so automation never compares half ranges
    def CheckBadArgs(self) -> None:
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Alpha.py", KCleanSource)
            BaseRef = FixtureInfo.CommitAll("base")
            ResultInfo = RunModule(RootPath, BaseRef)
        self.assertEqual(ResultInfo.returncode, 2)


# the kept reason contract needs boundary coverage so invalid owned sources fail at the command boundary
def CheckKeptReason() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        FixtureInfo = RepoFixture(RootPath)
        FixtureInfo.WriteFile("Alpha.py", KCleanSource)
        BaseRef = FixtureInfo.CommitAll("base")
        FixtureInfo.WriteFile(
            "Alpha.py", KCleanSource.replace("Value * 2", "Value * 3")
        )
        FixtureInfo.WriteFile("Bravo.py", KCleanSource)
        HeadRef = FixtureInfo.CommitAll("head")
        ResultInfo = RunModule(RootPath, BaseRef, HeadRef)
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    assert "passed" in ResultInfo.stdout


# a required rationale must be accepted while unrelated explanations still fail
def CheckNewReason() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        FixtureInfo = RepoFixture(RootPath)
        FixtureInfo.WriteFile("Alpha.py", KCleanSource)
        BaseRef = FixtureInfo.CommitAll("base")
        FixtureInfo.WriteFile("Bravo.py", KCleanSource)
        HeadRef = FixtureInfo.CommitAll("add rationale")
        PassedInfo = RunModule(RootPath, BaseRef, HeadRef)
        FixtureInfo.WriteFile(
            "Bravo.py", KCleanSource + "\n# this comment explains nothing\n"
        )
        HeadRef = FixtureInfo.CommitAll("add stray comment")
        FailedInfo = RunModule(RootPath, BaseRef, HeadRef)
    assert PassedInfo.returncode == 0, PassedInfo.stdout
    assert FailedInfo.returncode == 1, FailedInfo.stderr
    assert "Bravo.py:6:1: CMT002" in FailedInfo.stdout


# every declaration form must fail through the command boundary when its required reason disappears
@TestMarks.parametrize(
    "SourceText",
    (
        "class Model:\n    pass\n",
        "def Compute():\n    return 1\n",
        "async def FetchData():\n    return 1\n",
        "@staticmethod\ndef Compute():\n    return 1\n",
        "KResult = 1\n",
        "KResult: int = 1\n",
        "from pathlib import Path\n\nLegacyPath = Path\n",
        "KCallback = lambda Value: Value\n",
        "\n# nested scopes need coverage so local helpers cannot silently lose their purpose\n"
        + "def OuterCall():\n    def InnerCall():\n        return 1\n"
        + "    return InnerCall()\n",
        "\n# callable behavior needs coverage so inline callbacks retain their ordering purpose\n"
        + "def OrderValues(Values):\n    return sorted(Values, key=lambda Value: -Value)\n",
        "if True:\n    KResult = 1\n",
    ),
)
def CheckNoReasons(TmpPath: FilePath, SourceText: str) -> None:
    FixtureInfo = RepoFixture(TmpPath)
    FixtureInfo.WriteFile("Alpha.py", SourceText)
    _ = FixtureInfo.CommitAll("missing reason")
    ResultInfo = RunModule(TmpPath)
    assert ResultInfo.returncode == 1, ResultInfo.stdout + ResultInfo.stderr
    assert "Alpha.py:" in ResultInfo.stdout
    assert "RAT001" in ResultInfo.stdout


# existing debt must remain visible even when another change leaves its file untouched
def CheckDebt(TmpPath: FilePath) -> None:
    FixtureInfo = RepoFixture(TmpPath)
    FixtureInfo.WriteFile("Legacy.py", KBadSource)
    _ = FixtureInfo.CommitAll("legacy debt")
    FixtureInfo.WriteFile("Alpha.py", KCleanSource)
    FixtureInfo.WriteFile(
        "tools/steering/SteeringBaseline.txt",
        "Legacy.py\tRAT001\tdeclaration needs a rationale comment\n",
    )
    _ = FixtureInfo.CommitAll("unrelated change and baseline")
    ResultInfo = RunModule(TmpPath)
    assert ResultInfo.returncode == 1, ResultInfo.stdout + ResultInfo.stderr
    assert "Legacy.py:1:1: RAT001" in ResultInfo.stdout
    assert "Alpha.py:" not in ResultInfo.stdout


# syntax and placement rules need process coverage so restoration cannot accept mechanically valid explanations
@TestMarks.parametrize(
    "SourceText,RuleCode",
    (
        (
            "import math\n# shared math exists so callers agree on one contract\nKValue = 1\n",
            "RAT002",
        ),
        ("# too short\nKValue = 1\n", "RAT003"),
        (
            "# Shared math exists so callers agree on one contract\nKValue = 1\n",
            "RAT003",
        ),
        (
            "# shared math exists so callers agree on one contract.\nKValue = 1\n",
            "RAT003",
        ),
        ("# returns the input value multiplied by two\nKValue = 1\n", "RAT004"),
    ),
)
def CheckTextRules(TmpPath: FilePath, SourceText: str, RuleCode: str) -> None:
    FixtureInfo = RepoFixture(TmpPath)
    FixtureInfo.WriteFile("Alpha.py", SourceText)
    _ = FixtureInfo.CommitAll("invalid reason")
    ResultInfo = RunModule(TmpPath)
    assert ResultInfo.returncode == 1, ResultInfo.stdout + ResultInfo.stderr
    assert RuleCode in ResultInfo.stdout


# only repository root exclusions may bypass enforcement so nested owned packages cannot hide missing rationale
def CheckRootScope(TmpPath: FilePath) -> None:
    FixtureInfo = RepoFixture(TmpPath)
    for Folder in ("re", "examples", "modules", "Parashell"):
        FixtureInfo.WriteFile(f"{Folder}/External.py", KBadSource)
        FixtureInfo.WriteFile(f"src/{Folder}/Owned.py", KBadSource)
    _ = FixtureInfo.CommitAll("root and nested scope")
    ResultInfo = RunModule(TmpPath)
    assert ResultInfo.returncode == 1, ResultInfo.stdout + ResultInfo.stderr
    for Folder in ("re", "examples", "modules", "Parashell"):
        assert f"src/{Folder}/Owned.py:" in ResultInfo.stdout
        assert f"{Folder}/External.py:" not in ResultInfo.stdout
