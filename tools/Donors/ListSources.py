from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path as FilePath

# the skip folders vocabulary must stay centralized so payload policy agrees on supported native identities
KSkipFolders = frozenset({"__pycache__", ".venv", "build", "dist"})


# list sources needs an explicit validity boundary so captured document data cannot become production writer input
def ListSources(PathValues: Sequence[str]) -> list[FilePath]:
    SourceSet: set[FilePath] = set()
    for PathValue in PathValues:
        InputPath = FilePath(PathValue).resolve()
        if not InputPath.exists():
            raise FileNotFoundError(f"path does not exist: {PathValue}")
        if InputPath.is_file():
            SourceSet.add(InputPath)
            continue
        SourceSet.update(
            SourcePath.resolve()
            for SourcePath in InputPath.rglob("*.py")
            if not KSkipFolders.intersection(SourcePath.relative_to(InputPath).parts)
        )
    return sorted(SourceSet)
