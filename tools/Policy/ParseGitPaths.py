# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import os as OsTools

from tools.Policy.GitFailure import GitFailure


# strict nul parsing preserves every legal whitespace character inside tracked git paths
def ParseGitPaths(PathData: bytes) -> tuple[str, ...]:
    if not PathData:
        return ()
    if not PathData.endswith(b"\0"):
        raise GitFailure("git path output was not terminated by a nul byte")
    ByteParts = PathData[:-1].split(b"\0")
    if any(not PathBytes for PathBytes in ByteParts):
        raise GitFailure("git path output contained an empty path record")
    return tuple(OsTools.fsdecode(PathBytes) for PathBytes in ByteParts)
