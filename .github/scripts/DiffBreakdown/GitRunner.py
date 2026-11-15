from __future__ import annotations

import subprocess as Subprocess
from pathlib import Path as FilePath

from GitEnviron import BuildGitEnv
from RequireSha import RequireSha

# the git options order must stay explicit so published evidence stays bound to the reviewed revision
KGitOptions = ("-c", "core.hooksPath=/dev/null", "-c", "diff.renameLimit=1000")

# the fetch options order must stay explicit so published evidence stays bound to the reviewed revision
KFetchOptions = ("--filter=blob:none", "--no-tags", "--no-recurse-submodules")


# the git runner contract needs a dedicated boundary so published evidence stays bound to the reviewed revision
class GitRunner:

    # git runner needs explicit initial state so published evidence stays bound to the reviewed revision
    def __init__(self, RootPath: FilePath) -> None:
        self.RootPath = RootPath
        self.EnvValues = BuildGitEnv()

    # the git operation needs one orchestration boundary so published evidence stays bound to the reviewed revision
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

    # the text operation needs a distinct decoding boundary so published evidence stays bound to the reviewed revision
    def ReadText(self, *ArgList: str) -> str:
        return self.RunGit(*ArgList).stdout.decode().strip()

    # the commit decision must stay consistent so published evidence stays bound to the reviewed revision
    def HasCommit(self, CommitSha: str) -> bool:
        ObjectName = RequireSha(CommitSha) + "^{commit}"
        return (
            self.RunGit("cat-file", "-e", ObjectName, IsChecked=False).returncode == 0
        )

    # the fetch commit contract needs a shared interpretation so published evidence stays bound to the reviewed revision
    def FetchCommit(self, CommitSha: str) -> None:
        IsShallow = self.ReadText("rev-parse", "--is-shallow-repository") == "true"
        if not IsShallow and self.HasCommit(CommitSha):
            return
        ShallowArgs = ["--unshallow"] if IsShallow else []
        self.RunGit(
            "fetch", *ShallowArgs, *KFetchOptions, "origin", RequireSha(CommitSha)
        )

    # find merge base must resolve unambiguously so published evidence stays bound to the reviewed revision
    def FindMergeBase(self, BaseSha: str, HeadSha: str) -> str:
        return self.ReadText("merge-base", RequireSha(BaseSha), RequireSha(HeadSha))

    # the ancestor decision must stay consistent so published evidence stays bound to the reviewed revision
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
