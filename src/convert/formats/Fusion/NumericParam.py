# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from re import fullmatch as MatchFull
from struct import unpack as Unpack

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativeParam import NativeParam

# registered classes keep numeric parameter recognition independent of text heuristics
KParamGuid = "7A6A3D31-BE74-4E19-9115-20642944C2E4"


# the supported numeric dialect carries an optional reciprocal binding reference
def ReadParamBind(Cursor: MetaCursor) -> int | None:
    TagValue = Cursor.TakeBytes(1)
    if TagValue == b"\0":
        return None
    if TagValue != b"\1":
        raise ValueError("Invalid Fusion parameter binding tag")
    BindingId = Cursor.ReadLong()
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Invalid Fusion parameter binding suffix")
    return BindingId


# the newer zero extension is accepted only for the observed bound numeric layout
def ReadRoleField(Cursor: MetaCursor, BindingId: int | None) -> tuple[str, bytes]:
    Metadata = Cursor.TakeBytes(10)
    if Metadata[:4] != bytes(4):
        raise ValueError("Unsupported Fusion parameter value type")
    RoleStart = Cursor.Offset
    try:
        return Cursor.ReadText(True, Maximum=1024), Metadata
    except ValueError:
        if BindingId is None or Metadata != bytes(10):
            raise
        Cursor.Offset = RoleStart
        ExtraByte = Cursor.TakeBytes(1)
        if ExtraByte != b"\0":
            raise ValueError("Unsupported Fusion parameter metadata extension")
        return Cursor.ReadText(True, Maximum=1024), Metadata + ExtraByte


# native numeric values require complete record framing before entering the document model
def ReadNativeNum(BodyValue: bytes) -> NativeParam:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(12) != bytes(7) + b"\x06" + bytes(4):
        raise ValueError("Unsupported Fusion parameter header")
    Comment = Cursor.ReadText(True, Maximum=1024, AllowControls=True)
    NativeIndex = Cursor.ReadWord()
    BindingId = ReadParamBind(Cursor)
    Formula = Cursor.ReadText(True, Maximum=1024)
    RoleName, Metadata = ReadRoleField(Cursor, BindingId)
    Reserved = Cursor.ReadText(True, Maximum=1024)
    DisplayUnit = Cursor.ReadText(True, Maximum=1024)
    ParamName = Cursor.ReadText(True, Maximum=1024)
    if not RoleName or Reserved or not MatchFull(r"[A-Za-z_][A-Za-z_0-9]*", ParamName):
        raise ValueError("Invalid Fusion numeric parameter fields")
    if BindingId is None and (
        RoleName != "User Parameter" or Metadata[7] not in (0, 1)
    ):
        raise ValueError("Unsupported Fusion user parameter layout")
    Number = float(Unpack("<d", Cursor.TakeBytes(8))[0])
    if not IsFinite(Number):
        raise ValueError("Non-finite Fusion numeric parameter")
    if Cursor.TakeBytes(12) != b"\0\1\x10" + bytes(9) or Cursor.Offset != len(
        BodyValue
    ):
        raise ValueError("Unsupported Fusion numeric parameter trailer")
    return NativeParam(
        RoleName,
        ParamName,
        DisplayUnit,
        Number,
        Formula,
        Comment,
        BindingId,
        NativeIndex,
        Metadata,
    )
