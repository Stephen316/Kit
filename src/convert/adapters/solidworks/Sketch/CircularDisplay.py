# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose

from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.CircularRecords import (
    RoundDiameter,
    CircularHeader,
    CircularView,
    RadialHandle,
    RadialSuffix,
)
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayFields import (
    ReadCache,
    ReadEmptyTexts,
    ReadNulls,
)
from convert.adapters.solidworks.Sketch.Displays import TakeShownClass
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# connect the displayed radial handle to the active sketch and its sole driving value
def ReadRadialLink(Cursor: ArchiveCursor, SketchNode: int) -> RadialHandle:
    Cursor.ReadNull()
    Style = Cursor.ReadValue("<d2ihf2ihf8ihf5i")
    RequireArch(Style[-5:] == (0, 0, 0, 0, 4), True, "unexpected radial visual mode")
    RequireArch(
        Cursor.ReadPoint(12) == (0,) * 12, True, "unexpected radial position array"
    )
    RequireArch(
        Cursor.ReadInts("<i") == (2,), True, "unexpected radial display direction count"
    )
    _ = Cursor.ReadPoint(6)
    ReadEmptyTexts(Cursor, 1)
    TextPoint = Cursor.ReadPoint(3)
    RequireArch(
        Cursor.ReadInts("<i") == (17,), True, "expected radial display wire kind"
    )
    Cursor.ReadNull()
    Settings = Cursor.ReadValue("<i4d4i2diH3id2i")
    RequireArch(
        Settings[11:16] == (0, 0, 0, 0, 0) and Settings[-2:] == (0, 1),
        True,
        "unexpected radial display handle route",
    )
    StartOffset = Cursor.Offset
    TakeShownClass(Cursor, "moSkDimHandleRadial_c")
    Handle = Cursor.NextIndex - 1
    SlotValue = ReadDimHandle(Cursor, SketchNode)
    RequireArch(SlotValue == 0, True, "radial display does not reach the sole G1 value")
    return {
        "span": [StartOffset, Cursor.Offset],
        "object": Handle,
        "sketch_object": SketchNode,
        "g1_slot": SlotValue,
        "text_point_m": TextPoint,
    }


# confirm that both measured display caches describe the owned diameter
def ReadValueCaches(Cursor: ArchiveCursor, Diameter: float) -> tuple[float, float]:
    RequireArch(
        Cursor.ReadInts("<3H") == (0, 0, 0), True, "unexpected radial display groups"
    )
    RequireArch(Cursor.ReadText() == "<MOD-DIAM>", True, "missing saved diameter label")
    ReadEmptyTexts(Cursor, 3)
    _ = Cursor.ReadPoint(22)
    _ = Cursor.ReadInts("<i7H")
    _ = Cursor.ReadPoint(3)
    Copies = ReadCache(Cursor)
    RequireArch(
        all(IsClose(Value, Diameter, rel_tol=0, abs_tol=1e-9) for Value in Copies),
        True,
        "saved radial display caches disagree with the driving value",
    )
    return Copies


# reach the subtype specific return through the framed common display fields
def ReadViewTail(Cursor: ArchiveCursor) -> None:
    TakeShownClass(Cursor, "moFavoriteHandle_c")
    Appearance = Cursor.ReadValue("<2iId2HI4didHi30Id")
    RequireArch(
        Appearance[:6] == (0, -1, 0, -1, 1, 1),
        True,
        "unexpected radial display favorite",
    )
    ReadEmptyTexts(Cursor, 4)
    _ = Cursor.ReadInts("<2HiI")
    ReadNulls(Cursor, 3)
    RequireArch(
        Cursor.ReadInts("<I") == (1002101,), True, "unexpected radial display flags"
    )
    ReadNulls(Cursor, 2)
    RequireArch(
        Cursor.ReadInts("<3i") == (0, 0, 0), True, "unexpected additional display items"
    )
    Cursor.ReadNull()
    _ = Cursor.ReadValue("<5id6i")
    ReadEmptyTexts(Cursor, 2)
    _ = Cursor.ReadInts("<3i")
    ReadEmptyTexts(Cursor, 1)
    _ = Cursor.ReadValue("<2i3d2i")
    ReadEmptyTexts(Cursor, 1)


# recognize the witnessed radial return and leave the appearance flags uninterpreted
def ReadRadialTail(Cursor: ArchiveCursor) -> RadialSuffix:
    StartOffset = Cursor.Offset
    (Flags,) = Cursor.ReadInts("<i")
    RequireArch(
        Cursor.ReadPoint(12) == (0,) * 12, True, "unexpected auxiliary radial placement"
    )
    RequireArch(
        Cursor.ReadInts("<i") == (0,), True, "unexpected radial label collection"
    )
    Cursor.ReadNull()
    ReadEmptyTexts(Cursor, 1)
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<i") == (0,), True, "unexpected auxiliary radial transform"
    )
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i") == (0,), True, "unexpected radial helper flags")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i") == (0,), True, "unexpected radial display return")
    return {"span": [StartOffset, Cursor.Offset], "raw_flags": Flags}


# continue from the common display object to the circular sketch environment
def ReadRadialView(
    Cursor: ArchiveCursor, Profile: CircularHeader, Diameter: RoundDiameter
) -> CircularView:
    Handle = ReadRadialLink(Cursor, Profile["sketch_node"])
    CopyValues = ReadValueCaches(Cursor, Diameter["diameter_m"])
    ReadViewTail(Cursor)
    Suffix = ReadRadialTail(Cursor)
    return {"handle": Handle, "diameter_cache_m": CopyValues, "radial_suffix": Suffix}
