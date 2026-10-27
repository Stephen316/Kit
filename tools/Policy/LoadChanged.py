# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from pathlib import Path as FilePath

from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand


# destination only diffs let renamed files satisfy policy without judging deleted source names
def LoadChanged(
    RootPath: FilePath,
    BaseRef: str,
    HeadRef: str,
) -> tuple[str, ...]:
    OutputData = RunGitCommand(
        RootPath,
        [
            "diff",
            "--name-only",
            "-z",
            "--find-renames",
            "--diff-filter=ACMRTUXB",
            "--end-of-options",
            BaseRef,
            HeadRef,
            "--",
            ":(top)",
        ],
    )
    return ParseGitPaths(OutputData)
