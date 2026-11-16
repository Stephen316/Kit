import hashlib as Hashlib
import json as JsonCodec
import os as OsModule
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

import pytest as Pytest


# real git objects keep audit coverage independent from mocked repository answers
def GitValue(
    RootPath: FilePath, ArgList: list[str], InputText: str | None = None
) -> str:
    Process = Subprocess.run(
        [
            "git",
            "-C",
            str(RootPath),
            "-c",
            "user.name=Audit Fixture",
            "-c",
            "user.email=audit@example.invalid",
            *ArgList,
        ],
        input=InputText,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    return Process.stdout.strip()


# capture identity must remain observable without opening native document contents
def CaptureTree(RootPath: FilePath, NativeBlob: str, KeepSecond: bool) -> str:
    CaptureRows = f"100644 blob {NativeBlob}\tP03-solidworks-baseline-a.SLDPRT\n"
    if KeepSecond:
        CaptureRows += f"100644 blob {NativeBlob}\tP03-solidworks-baseline-b.SLDPRT\n"
    LeafTree = GitValue(RootPath, ["mktree"], CaptureRows)
    FamilyTree = GitValue(
        RootPath, ["mktree"], f"040000 tree {LeafTree}\tsolidworks-aaaaaaaaaaaa\n"
    )
    RecipeTree = GitValue(RootPath, ["mktree"], f"040000 tree {FamilyTree}\tP03\n")
    CaptureRoot = GitValue(
        RootPath, ["mktree"], f"040000 tree {RecipeTree}\tPairedCaptures\n"
    )
    return GitValue(RootPath, ["mktree"], f"040000 tree {CaptureRoot}\tautomation\n")


# retained ancestry must remain distinguishable after its forbidden path leaves the final tree
def SeedHistory(RootPath: FilePath) -> tuple[str, str, str, str]:
    _ = GitValue(RootPath, ["init", "--bare"])
    NativeBlob = GitValue(
        RootPath,
        ["hash-object", "-w", "--stdin"],
        "independently authored metadata fixture",
    )
    SourceBlob = GitValue(
        RootPath, ["hash-object", "-w", "--stdin"], "baseline source\n"
    )
    ResearchTree = CaptureTree(RootPath, NativeBlob, True)
    InitialTree = GitValue(
        RootPath,
        ["mktree"],
        f"100644 blob {SourceBlob}\tProbe.py\n040000 tree {ResearchTree}\tre\n",
    )
    FirstCommit = GitValue(
        RootPath, ["commit-tree", InitialTree, "-m", "initial fixture"]
    )
    SecondTree = GitValue(
        RootPath,
        ["mktree"],
        f"100644 blob {SourceBlob}\tProbe.py\n100644 blob {NativeBlob}\tIndependent.DLL\n040000 tree {ResearchTree}\tre\n",
    )
    UnsafeCommit = GitValue(
        RootPath,
        [
            "commit-tree",
            SecondTree,
            "-p",
            FirstCommit,
            "-m",
            "independent named marker",
        ],
    )
    SourceText = f"FIRST = '{FirstCommit}'\nUNSAFE = '{UnsafeCommit}'\nNATIVE = '{NativeBlob}'\nTREE = '{InitialTree}'\nABSENT = '{'f' * 40}'\nSHA256 = '{'a' * 64}'\n"
    CurrentBlob = GitValue(RootPath, ["hash-object", "-w", "--stdin"], SourceText)
    CurrentTree = CaptureTree(RootPath, NativeBlob, False)
    FinalTree = GitValue(
        RootPath,
        ["mktree"],
        f"100644 blob {CurrentBlob}\tProbe.py\n040000 tree {CurrentTree}\tre\n",
    )
    FinalCommit = GitValue(
        RootPath,
        ["commit-tree", FinalTree, "-p", UnsafeCommit, "-m", "remove named marker"],
    )
    return FirstCommit, UnsafeCommit, FinalCommit, NativeBlob


# the standalone audit must preserve exact pins despite replacement refs and working files
def CheckAuditFlow(TmpPath: FilePath) -> None:
    FirstCommit, UnsafeCommit, FinalCommit, NativeBlob = SeedHistory(TmpPath)
    _ = GitValue(TmpPath, ["replace", UnsafeCommit, FirstCommit])
    RootPath = FilePath(__file__).resolve().parents[3]
    Command = [
        System.executable,
        str(RootPath / "re/automation/HistoryInputAudit.py"),
        "--root",
        str(TmpPath),
        "--revision",
        FinalCommit,
        "--main",
        FirstCommit,
        "--path",
        "Probe.py",
    ]
    Process = Subprocess.run(
        Command,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={**OsModule.environ, "GIT_DIR": str(TmpPath / "unrelated.git")},
    )
    assert Process.returncode == 0, Process.stderr
    Report = JsonCodec.loads(Process.stdout)
    Objects = {Entry["sha"]: Entry for Entry in Report["objects"]}
    assert Report["revision"] == FinalCommit and Report["main_revision"] == FirstCommit
    assert Report["summary"]["object_types"] == {
        "blob": 1,
        "commit": 2,
        "missing": 1,
        "tree": 1,
    }
    assert Report["summary"]["commits_with_prohibited_paths"] == 1
    assert Objects[FirstCommit]["main_reachability"] == "ancestor"
    assert Objects[UnsafeCommit]["main_reachability"] == "not_ancestor"
    assert Objects[UnsafeCommit]["prohibited_paths"] == ["Independent.DLL"]
    assert Objects[UnsafeCommit]["capture_states"] == {"missing": 1, "unchanged": 1}
    assert Objects[NativeBlob]["head_paths"] == [
        "re/automation/PairedCaptures/P03/solidworks-aaaaaaaaaaaa/P03-solidworks-baseline-a.SLDPRT"
    ]
    assert Objects[UnsafeCommit]["references"] == [
        {"path": "Probe.py", "line": 2, "byte_column": 11}
    ]
    Checksum = Report.pop("report_sha256")
    assert (
        Checksum
        == Hashlib.sha256(
            JsonCodec.dumps(
                Report, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()
    )
    _ = (TmpPath / "Probe.py").write_text("untracked replacement\n", encoding="utf-8")
    Repeated = Subprocess.run(
        Command, capture_output=True, text=True, check=False, timeout=120
    )
    assert Repeated.returncode == 0 and Repeated.stdout == Process.stdout


# invalid selectors must fail before git can interpret them as revisions or external paths
@Pytest.mark.parametrize("ArgList", (("--path", "../outside.py"), ("--revision=-bad",)))
def CheckAuditArgs(TmpPath: FilePath, ArgList: tuple[str, ...]) -> None:
    FirstCommit, _, FinalCommit, _ = SeedHistory(TmpPath)
    RootPath = FilePath(__file__).resolve().parents[3]
    Process = Subprocess.run(
        [
            System.executable,
            str(RootPath / "re/automation/HistoryInputAudit.py"),
            "--root",
            str(TmpPath),
            "--revision",
            FinalCommit,
            "--main",
            FirstCommit,
            *ArgList,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 1
    assert Process.stdout == "" and "history input audit refused" in Process.stderr


# oversized tracked source must be refused without loading its full contents into the audit
def CheckAuditLimit(TmpPath: FilePath) -> None:
    _ = GitValue(TmpPath, ["init", "--bare"])
    LargeBlob = GitValue(
        TmpPath, ["hash-object", "-w", "--stdin"], "x" * (4 * 1024 * 1024 + 1)
    )
    LargeTree = GitValue(TmpPath, ["mktree"], f"100644 blob {LargeBlob}\tLarge.py\n")
    Revision = GitValue(TmpPath, ["commit-tree", LargeTree, "-m", "oversized source"])
    RootPath = FilePath(__file__).resolve().parents[3]
    Process = Subprocess.run(
        [
            System.executable,
            str(RootPath / "re/automation/HistoryInputAudit.py"),
            "--root",
            str(TmpPath),
            "--revision",
            Revision,
            "--main",
            Revision,
            "--path",
            "Large.py",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 1 and Process.stdout == ""
    assert "file or byte limits" in Process.stderr
