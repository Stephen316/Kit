# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from pathlib import PurePosixPath as PosixPath

from tools.Policy.PolicyRules import KBinarySuffixes
from tools.Policy.PolicyRules import KStandardNames
from tools.Policy.PolicyRules import KToolPathSet


# narrow identity checks protect required tool and binary names without hiding neighboring files
def IsNameExempt(RepoPath: str) -> bool:
    PathInfo = PosixPath(RepoPath)
    PathParts = PathInfo.parts
    if RepoPath in KToolPathSet or PathInfo.name in KStandardNames:
        return True
    if (
        len(PathParts) == 4
        and PathParts[:2] == (".agents", "skills")
        and PathInfo.name == "SKILL.md"
    ):
        return True
    if len(PathParts) >= 3 and PathParts[:2] == (".kiro", "skills"):
        return True
    return (
        len(PathParts) >= 3
        and PathParts[:2] == ("re", "binaries")
        and PathInfo.suffix.lower() in KBinarySuffixes
    )
