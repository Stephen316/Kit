# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
