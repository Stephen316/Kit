# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Iterable

from tools.Policy.CheckDirCounts import CheckDirCounts
from tools.Policy.CheckNamePaths import CheckNamePaths
from tools.Policy.PathFinding import PathFinding


# one composition point keeps full tree and changed destination enforcement behavior aligned
def CheckPathPolicy(
    TrackedPaths: Iterable[str],
    TargetPaths: Iterable[str] | None = None,
) -> list[PathFinding]:
    TrackedSet = set(TrackedPaths)
    TargetSet = TrackedSet if TargetPaths is None else set(TargetPaths) & TrackedSet
    FindingList = CheckNamePaths(TargetSet)
    FindingList.extend(CheckDirCounts(TrackedSet, TargetSet))
    return sorted(FindingList)
