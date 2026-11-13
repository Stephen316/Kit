from __future__ import annotations

from fnmatch import fnmatchcase as MatchName


def IsPartsMatch(
    PatternParts: tuple[str, ...], PathParts: tuple[str, ...], NeedsChild: bool
) -> bool:
    if not PatternParts:
        return bool(PathParts) or not NeedsChild
    if PatternParts[0] == "**":
        return any(
            IsPartsMatch(PatternParts[1:], PathParts[Offset:], NeedsChild)
            for Offset in range(len(PathParts) + 1)
        )
    return (
        bool(PathParts)
        and MatchName(PathParts[0], PatternParts[0])
        and IsPartsMatch(PatternParts[1:], PathParts[1:], NeedsChild)
    )


def IsGlobMatch(PatternText: str, RepoPath: str) -> bool:
    NeedsChild = PatternText.endswith("/")
    IsAnchored = PatternText.startswith("/") or "/" in PatternText.rstrip("/")
    PatternParts = tuple(PartText for PartText in PatternText.split("/") if PartText)
    PathParts = tuple(RepoPath.split("/"))
    Starts = range(1 if IsAnchored else len(PathParts))
    return any(
        IsPartsMatch(PatternParts, PathParts[Start:], NeedsChild) for Start in Starts
    )
