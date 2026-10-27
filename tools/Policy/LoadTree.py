# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from pathlib import Path as FilePath

from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand


# changed scans need the exact head tree so directory counts ignore checkout drift
def LoadTree(RootPath: FilePath, HeadRef: str) -> tuple[str, ...]:
    OutputData = RunGitCommand(
        RootPath,
        [
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            "--full-tree",
            "--end-of-options",
            HeadRef,
        ],
    )
    return ParseGitPaths(OutputData)
