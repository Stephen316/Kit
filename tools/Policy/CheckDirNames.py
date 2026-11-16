from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath as PosixPath

from tools.Policy.CompatDirs import KCompatDirs
from tools.Policy.IsValidStem import IsValidStem
from tools.Policy.PathFinding import PathFinding
from tools.Policy.PolicyRules import KCodeRoots


# ancestor checks prevent valid filenames from concealing noncompliant internal package directories
def CheckDirNames(TargetPaths: Iterable[str]) -> list[PathFinding]:
    FolderPaths = {
        FolderPath
        for RepoPath in TargetPaths
        for FolderPath in PosixPath(RepoPath).parents
        if len(FolderPath.parts) > 1 and FolderPath.parts[0] in KCodeRoots
    }
    FindingList: list[PathFinding] = []
    for FolderPath in sorted(FolderPaths):
        FolderText = str(FolderPath)
        if FolderText in KCompatDirs or IsValidStem(FolderPath.name):
            continue
        MessageText = (
            f"directory name {FolderPath.name!r} must match ^[A-Z][A-Za-z]*$ "
            "and contain no digits"
        )
        FindingList.append(PathFinding(FolderText, "PTH003", MessageText))
    return FindingList
