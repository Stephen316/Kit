# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from tools.Policy.PathFinding import PathFinding


# escaped paths keep each diagnostic on one line even for unusual legal filenames
def FormatFinding(FindingInfo: PathFinding) -> str:
    return (
        f"{FindingInfo.RepoPath!r}: {FindingInfo.RuleCode}: "
        f"{FindingInfo.MessageText}"
    )
