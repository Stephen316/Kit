from __future__ import annotations

import os as OsLib

# the access mask variants need one shared contract so test reuse cannot omit a supported value shape
KAccessMask = OsLib.O_RDONLY | OsLib.O_WRONLY | OsLib.O_RDWR


# the read open decision must stay consistent so dependency changes cannot revive stale passing results
def IsReadOpen(ModeValue: object, FlagValue: object) -> bool:
    if isinstance(ModeValue, str):
        return "r" in ModeValue or "+" in ModeValue
    if isinstance(FlagValue, int):
        return FlagValue & KAccessMask != OsLib.O_WRONLY
    return True
