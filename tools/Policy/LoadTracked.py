from __future__ import annotations

from pathlib import Path as FilePath

from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand


# full scans use the index so untracked build products never affect repository policy
def LoadTracked(RootPath: FilePath) -> tuple[str, ...]:
    OutputData = RunGitCommand(
        RootPath,
        ["ls-files", "--cached", "--full-name", "-z", "--", ":(top)"],
    )
    return ParseGitPaths(OutputData)
