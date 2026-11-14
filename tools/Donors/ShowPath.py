from __future__ import annotations

from pathlib import Path as FilePath


def ShowPath(SourcePath: FilePath) -> str:
    ResolvedPath = SourcePath.resolve()
    try:
        return ResolvedPath.relative_to(FilePath.cwd().resolve()).as_posix()
    except ValueError:
        return ResolvedPath.as_posix()
