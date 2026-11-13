from __future__ import annotations

import json as JsonLib
import os as OsLib
import shutil as ShellUtil
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture

KRootPath = FilePath(__file__).resolve().parents[2]
KEngineRel = FilePath(".github/scripts/DiffBreakdown")
KConfigRels = (
    FilePath(".github/config/DiffBreakdown.json"),
    FilePath(".github/config/DiffRules.txt"),
)
KBaseFiles = {
    "Documentation/Guide.md": "one\ntwo\nthree\n",
    "README.md": "Kit\n",
    "re/Notes.py": "Probe = 1\n",
    "src/Module.py": "Value = 1\n",
    "tests/Policy/SampleTests.py": "Sample = 1\n",
    "tools/Sample.py": "Sample = 1\n",
    "Spaced.py": "Alpha = 1\n",
    "Old/Name.txt": "moved\ncontent\nkept\n",
}
KHeadFiles = {
    "Documentation/Guide.md": "one\ntwo\nthree\nfour\nfive\nsix\nseven\n",
    "README.md": "Kit\nconverter\n",
    "re/Notes.py": "Probe = 1\nProbe = 2\nProbe = 3\nProbe = 4\n",
    "re/Readme.md": "scratch\nnotes\n",
    "src/Module.py": "Value = 2\n",
    "tests/Policy/SampleTests.py": "Sample = 1\nSample = 2\n",
    "tools/Sample.py": "Sample = 1\nSample = 2\n",
    ".github/workflows/Sample.yml": "name: Sample\non: push\n",
    ".github/README.md": "github\n",
    ".agents/skills/Sample/SKILL.md": "skill\n",
    "AGENTS.md": "agents\n",
    "Spaced.py": "Alpha =  1\n",
    "pyproject.toml": "[project]\n",
}
KExpectedTypes = {
    "Documentation/Guide.md": "Documentation",
    "README.md": "Documentation",
    "re/Notes.py": "Reverse Engineering",
    "re/Readme.md": "Reverse Engineering",
    "src/Module.py": "Source",
    "tests/Policy/SampleTests.py": "Tests",
    "tools/Sample.py": "Tools",
    ".github/workflows/Sample.yml": "GitHub",
    ".github/README.md": "GitHub",
    ".agents/skills/Sample/SKILL.md": "Agents",
    "AGENTS.md": "Agents",
    "Spaced.py": "Whitespace Only",
    "pyproject.toml": "Unclassified",
    "Image.bin": "Binary Assets",
    "Fresh/Name.txt": "Unclassified",
}


def BuildFixture(RootPath: FilePath) -> tuple[RepoFixture, str, str]:
    _ = ShellUtil.copytree(
        KRootPath / KEngineRel,
        RootPath / KEngineRel,
        ignore=ShellUtil.ignore_patterns("__pycache__"),
    )
    (RootPath / KConfigRels[0]).parent.mkdir(parents=True, exist_ok=True)
    for ConfigRel in KConfigRels:
        _ = ShellUtil.copyfile(KRootPath / ConfigRel, RootPath / ConfigRel)
    FixtureInfo = RepoFixture(RootPath)
    for RepoPath, ContentText in KBaseFiles.items():
        FixtureInfo.WriteFile(RepoPath, ContentText)
    BaseRef = FixtureInfo.CommitAll("base")
    for RepoPath, ContentText in KHeadFiles.items():
        FixtureInfo.WriteFile(RepoPath, ContentText)
    _ = (RootPath / "Image.bin").write_bytes(b"\x00\x01\x02binary")
    (RootPath / "Fresh").mkdir()
    FixtureInfo.MoveFile("Old/Name.txt", "Fresh/Name.txt")
    return FixtureInfo, BaseRef, FixtureInfo.CommitAll("head")


def RunEngine(
    RootPath: FilePath, BaseRef: str, HeadRef: str, *ArgItems: str
) -> Subprocess.CompletedProcess[str]:
    EnvValues = {
        KeyText: ValueText
        for KeyText, ValueText in OsLib.environ.items()
        if KeyText not in {"GH_TOKEN", "GITHUB_TOKEN"}
    }
    EnvValues.update(
        GITHUB_REPOSITORY="TryUniCAD/Kit",
        GITHUB_EVENT_NAME="pull_request",
        GITHUB_SHA=HeadRef,
        GITHUB_RUN_ID="11",
        GITHUB_RUN_NUMBER="3",
        GITHUB_RUN_ATTEMPT="1",
        PULL_NUMBER="7",
        BASE_SHA=BaseRef,
        HEAD_SHA=HeadRef,
    )
    return Subprocess.run(
        [System.executable, str(RootPath / KEngineRel / "LaunchReport.py"), *ArgItems],
        cwd=RootPath,
        env=EnvValues,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def TestDiffPreview() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        _, BaseRef, HeadRef = BuildFixture(RootPath)
        RunResult = RunEngine(RootPath, BaseRef, HeadRef)
        assert RunResult.returncode == 0, RunResult.stdout + RunResult.stderr
        OutputPath = RootPath / "DiffBreakdownResults"
        Snapshot = JsonLib.loads((OutputPath / "Snapshot.json").read_text())
        ReportText = (OutputPath / "Report.md").read_text()
    FileTypes = {Entry["Path"]: Entry["Category"] for Entry in Snapshot["Files"]}
    assert FileTypes == KExpectedTypes
    Categories = Snapshot["Categories"]
    assert Categories["Documentation"]["Policy"] == "excluded"
    assert Categories["Reverse Engineering"]["Policy"] == "excluded"
    assert Categories["Source"]["Policy"] == "review"
    Totals = Snapshot["Totals"]
    assert Totals["Excluded"] == 10
    assert Totals["Reviewable"] + Totals["Excluded"] == Totals["Lines"]
    assert Totals["Binary"] == 1
    assert Snapshot["Publication"] == "preview"
    assert "Excluded from review" in ReportText
    assert "<!-- kit-diff-breakdown:v1:" in ReportText


def TestTrustGuard() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        _, BaseRef, HeadRef = BuildFixture(RootPath)
        RunResult = RunEngine(RootPath, BaseRef, HeadRef, "--publish")
    assert RunResult.returncode != 0
    assert "trusted pull_request_target revision" in RunResult.stderr
