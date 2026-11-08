# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose
from struct import unpack as Unpack

from convert.formats.Fusion.Extrudes.ExtrudeInputs import ExtrudeInputs
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptionalRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# symmetric distance can store either the total length or the length per side
KSymmetricModes = {1: "symmetric_full", 2: "symmetric_half"}


# operation and start framing exclude entity and surface controls from the distance grammar
def ReadExtrudeHead(
    Cursor: MetaCursor,
) -> tuple[int, int, tuple[float, float, float]]:
    if Cursor.TakeBytes(6) != b"\0\1" + bytes(4) or Cursor.TakeBytes(3) != bytes(3):
        raise ValueError("Unsupported Fusion Extrude prefix or entity start")
    if Cursor.ReadWord() != 4:
        raise ValueError("Fusion distance Extrude requires the NewBody operation")
    ModeCode = Cursor.ReadWord()
    if ModeCode not in (1, 2, 3) or Cursor.ReadWord() != (2 if ModeCode == 1 else 1):
        raise ValueError("Unsupported Fusion Extrude side mode")
    if Cursor.TakeBytes(2) != b"\0\1":
        raise ValueError("Fusion distance Extrude requires a solid profile")
    StartCode = Cursor.ReadWord()
    if StartCode not in (0, 1):
        raise ValueError("Unsupported Fusion Extrude start condition")
    AlongX, AlongY, AlongZ = Unpack("<3d", Cursor.TakeBytes(24))
    if not IsClose(
        AlongX * AlongX + AlongY * AlongY + AlongZ * AlongZ,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("Fusion Extrude direction is not a finite unit vector")
    return ModeCode, StartCode, (AlongX, AlongY, AlongZ)


# the active and inactive extent slots distinguish all four supported distance conventions
def ReadExtControls(Cursor: MetaCursor) -> ExtrudeInputs:
    ModeCode, StartCode, Direction = ReadExtrudeHead(Cursor)
    StartId = ReadOptionalRef(Cursor)
    AgainstId = ReadOptionalRef(Cursor)
    AlongId = ReadNativeRef(Cursor)
    CacheId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported second Fusion Extrude descriptor")
    TaperId = ReadOptionalRef(Cursor)
    if (
        Cursor.TakeBytes(1) != bytes(1)
        or Cursor.ReadWord() != 1
        or Cursor.TakeBytes(1) != bytes(1)
    ):
        raise ValueError("Unsupported Fusion Extrude first extent")
    if (
        Cursor.ReadWord(),
        Cursor.ReadWord(),
        Cursor.ReadWord(),
    ) != (0, int(ModeCode != 1), int(ModeCode == 2)):
        raise ValueError("Unsupported Fusion Extrude extent flags or second extent")
    if Cursor.TakeBytes(6) != bytes(6):
        raise ValueError("Unsupported Fusion Extrude second extent target or flags")
    SecondTaperId = ReadOptionalRef(Cursor)
    if (
        Cursor.TakeBytes(1) != bytes(1)
        or (StartId is not None) != (StartCode == 1)
        or (AgainstId is not None) != (ModeCode == 2)
        or (ModeCode == 1 and SecondTaperId is not None)
        or (ModeCode == 3 and SecondTaperId is not None and SecondTaperId != TaperId)
    ):
        raise ValueError("Fusion Extrude distance binding slots disagree")
    if ModeCode == 3:
        SideMode = KSymmetricModes.get(Cursor.ReadWord())
        if SideMode is None:
            raise ValueError("Unsupported Fusion symmetric Extrude distance convention")
    else:
        SideMode = "one_sided" if ModeCode == 1 else "two_sided"
    return ExtrudeInputs(
        AlongId,
        AgainstId,
        StartId,
        TaperId,
        SecondTaperId,
        SideMode,
        Direction,
        CacheId,
    )
