# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath as PosixPath

from tools.Policy.IsBroadSkip import IsBroadSkip
from tools.Policy.IsNameExempt import IsNameExempt
from tools.Policy.IsValidStem import IsValidStem
from tools.Policy.PathFinding import PathFinding


# target validation isolates actionable destination names while retaining exact repository paths
def CheckNamePaths(TargetPaths: Iterable[str]) -> list[PathFinding]:
    FindingList: list[PathFinding] = []
    for RepoPath in sorted(set(TargetPaths)):
        if IsBroadSkip(RepoPath) or IsNameExempt(RepoPath):
            continue
        StemText = PosixPath(RepoPath).stem
        if IsValidStem(StemText):
            continue
        MessageText = (
            f"file stem {StemText!r} must match ^[A-Z][A-Za-z]*$ "
            "and contain no digits"
        )
        FindingList.append(PathFinding(RepoPath, "PTH001", MessageText))
    return FindingList
