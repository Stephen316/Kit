from __future__ import annotations

import os as OsLib

KAccessMask = OsLib.O_RDONLY | OsLib.O_WRONLY | OsLib.O_RDWR


def IsReadOpen(ModeValue: object, FlagValue: object) -> bool:
    if isinstance(ModeValue, str):
        return "r" in ModeValue or "+" in ModeValue
    if isinstance(FlagValue, int):
        return FlagValue & KAccessMask != OsLib.O_WRONLY
    return True
