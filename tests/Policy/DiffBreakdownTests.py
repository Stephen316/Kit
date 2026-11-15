from __future__ import annotations

import json as JsonLib
import os as OsLib
import shutil as ShellUtil
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath

from tests.Policy.RepoFixture import RepoFixture

# root path needs a stable location so repository automation resolves inputs independently of the caller working directory
KRootPath = FilePath(__file__).resolve().parents[2]

# the engine rel cases must remain explicit so repository automation exercises the intended compatibility boundary
KEngineRel = FilePath(".github/scripts/DiffBreakdown")

# the config rels cases must remain explicit so repository automation exercises the intended compatibility boundary
KConfigRels = (
    FilePath(".github/config/DiffBreakdown.json"),
    FilePath(".github/config/DiffRules.txt"),
)

# the base files cases must remain explicit so repository automation exercises the intended compatibility boundary
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

# the head files cases must remain explicit so repository automation exercises the intended compatibility boundary
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

# the expected types cases must remain explicit so repository automation exercises the intended compatibility boundary
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


# shared build fixture setup keeps fixtures consistent so repository automation failures identify the intended compatibility boundary
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


# shared run engine setup keeps fixtures consistent so repository automation failures identify the intended compatibility boundary
def RunEngine(
    RootPath: FilePath,
    BaseRef: str,
    HeadRef: str,
    *ArgItems: str,
    Repository: str = "TryUniCAD/Kit",
) -> Subprocess.CompletedProcess[str]:
    EnvValues = {
        KeyText: ValueText
        for KeyText, ValueText in OsLib.environ.items()
        if KeyText not in {"GH_TOKEN", "GITHUB_TOKEN"}
    }
    EnvValues.update(
        GITHUB_REPOSITORY=Repository,
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


# the diff preview contract needs boundary coverage so the real command boundary enforces repository contracts
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


# the trust guard contract needs boundary coverage so the real command boundary enforces repository contracts
def TestTrustGuard() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        _, BaseRef, HeadRef = BuildFixture(RootPath)
        RunResult = RunEngine(RootPath, BaseRef, HeadRef, "--publish")
    assert RunResult.returncode != 0
    assert "trusted pull_request_target revision" in RunResult.stderr


# the repo guard contract needs boundary coverage so the real command boundary enforces repository contracts
def TestRepoGuard() -> None:
    with Tempfile.TemporaryDirectory() as TmpPath:
        RootPath = FilePath(TmpPath)
        _, BaseRef, HeadRef = BuildFixture(RootPath)
        for Repository in (
            "TryUniCAD/Kit/Extra",
            "TryUniCAD/",
            "/Kit",
            "Try UniCAD/Kit",
            "TryUniCAD/Kït",
        ):
            RunResult = RunEngine(RootPath, BaseRef, HeadRef, Repository=Repository)
            assert RunResult.returncode != 0, Repository
            assert "Invalid repository identity" in RunResult.stderr, Repository
        RunResult = RunEngine(
            RootPath, BaseRef, HeadRef, Repository="Try-UniCAD/Kit.io_2"
        )
        assert RunResult.returncode == 0, RunResult.stdout + RunResult.stderr
