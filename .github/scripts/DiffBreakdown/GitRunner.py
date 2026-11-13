from __future__ import annotations

import subprocess as Subprocess
from pathlib import Path as FilePath

from GitEnviron import BuildGitEnv
from RequireSha import RequireSha

KGitOptions = ("-c", "core.hooksPath=/dev/null", "-c", "diff.renameLimit=1000")
KFetchOptions = ("--filter=blob:none", "--no-tags", "--no-recurse-submodules")


class GitRunner:
    def __init__(self, RootPath: FilePath) -> None:
        self.RootPath = RootPath
        self.EnvValues = BuildGitEnv()

    def RunGit(
        self, *ArgList: str, IsChecked: bool = True
    ) -> Subprocess.CompletedProcess[bytes]:
        return Subprocess.run(
            ["git", *KGitOptions, *ArgList],
            cwd=self.RootPath,
            env=self.EnvValues,
            capture_output=True,
            check=IsChecked,
            timeout=40,
        )

    def ReadText(self, *ArgList: str) -> str:
        return self.RunGit(*ArgList).stdout.decode().strip()

    def HasCommit(self, CommitSha: str) -> bool:
        ObjectName = RequireSha(CommitSha) + "^{commit}"
        return (
            self.RunGit("cat-file", "-e", ObjectName, IsChecked=False).returncode == 0
        )

    def FetchCommit(self, CommitSha: str) -> None:
        IsShallow = self.ReadText("rev-parse", "--is-shallow-repository") == "true"
        if not IsShallow and self.HasCommit(CommitSha):
            return
        ShallowArgs = ["--unshallow"] if IsShallow else []
        self.RunGit(
            "fetch", *ShallowArgs, *KFetchOptions, "origin", RequireSha(CommitSha)
        )

    def FindMergeBase(self, BaseSha: str, HeadSha: str) -> str:
        return self.ReadText("merge-base", RequireSha(BaseSha), RequireSha(HeadSha))

    def IsAncestor(self, OldSha: str, NewSha: str) -> bool:
        ResultInfo = self.RunGit(
            "merge-base",
            "--is-ancestor",
            RequireSha(OldSha),
            RequireSha(NewSha),
            IsChecked=False,
        )
        if ResultInfo.returncode not in (0, 1):
            raise RuntimeError("Unable to establish commit ancestry")
        return ResultInfo.returncode == 0
