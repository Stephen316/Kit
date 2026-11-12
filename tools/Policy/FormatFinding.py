from __future__ import annotations

from tools.Policy.PathFinding import PathFinding


# escaped paths keep each diagnostic on one line even for unusual legal filenames
def FormatFinding(FindingInfo: PathFinding) -> str:
    return (
        f"{FindingInfo.RepoPath!r}: {FindingInfo.RuleCode}: "
        f"{FindingInfo.MessageText}"
    )
