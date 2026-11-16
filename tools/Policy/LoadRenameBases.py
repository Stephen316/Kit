from __future__ import annotations

from pathlib import Path as FilePath

from tools.Policy.GitFailure import GitFailure
from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand


# renamed sources need their original content so preserved comments retain real revision provenance
def LoadRenameBases(RootPath: FilePath, BaseRef: str, HeadRef: str) -> dict[str, str]:
    OutputData = RunGitCommand(
        RootPath,
        [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "-l0",
            "--diff-filter=R",
            "--end-of-options",
            BaseRef,
            HeadRef,
            "--",
            ":(top)",
        ],
    )
    RenameParts = ParseGitPaths(OutputData)
    if len(RenameParts) % 3:
        raise GitFailure("git rename output contained an incomplete record")
    return {
        RenameParts[IndexValue + 2]: RenameParts[IndexValue + 1]
        for IndexValue in range(0, len(RenameParts), 3)
    }
