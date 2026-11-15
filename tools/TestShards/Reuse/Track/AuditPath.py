from __future__ import annotations

import os as OsLib
from typing import cast as CastValue

from tools.TestShards.Reuse.Track.LocateFile import LocateFile


# the audit path contract needs a shared interpretation so dependency changes cannot revive stale passing results
def AuditPath(RootText: str, PathValue: object) -> str | None:
    RawValue: object = PathValue
    if isinstance(PathValue, OsLib.PathLike):
        RawValue = OsLib.fspath(CastValue("OsLib.PathLike[str]", PathValue))
    if isinstance(RawValue, bytes):
        RawValue = OsLib.fsdecode(RawValue)
    if not isinstance(RawValue, str):
        return None
    return LocateFile(RootText, OsLib.path.abspath(RawValue))
