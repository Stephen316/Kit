# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimFields import ReadDimFields
from convert.adapters.solidworks.Sketch.Geometry import ReadGeoSpansMut
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry
from convert.adapters.solidworks.Sketch.SketchTail import (
    ReadLogicalEnd,
    ReadRelationEnd,
    ReadSketchEnd,
)


# the native pair can be attributed to both lines without assigning a neutral law
@Dataclass(frozen=True, slots=True)
class PadLinePair:
    Start: int
    StopValue: int
    CodeValue: int
    Handles: tuple[int, int]
    Lines: tuple[int, int]


# each witnessed operand is one inline compact allocation of a local line handle
def ReadPadHandle(Cursor: SketchArchive) -> int:
    _, _, Index = Cursor.TakePointer(("sgLineHandle",), KClassRefKind, CompactOnly=True)
    Cursor.ReadPayload("sgLineHandle", Index)
    return Index


# the active logical relation must reach two distinct local perimeter line handles
def ReadPadPair(Cursor: SketchArchive, Geometry: SketchGeometry) -> PadLinePair:
    RequireArch(Cursor.ReadInts("<H"), (1,), "one upper-pad line relation")
    Start = Cursor.Offset
    RequireArch(ReadDimFields(Cursor, None), (-1, 0, 0), "upper-pad relation fields")
    CodeValue, Operands, Deleted, Reserved = Cursor.ReadInts("<i3H")
    RequireArch(
        (CodeValue, Operands, Deleted, Reserved),
        (14, 2, 0, 0),
        "active type-14 line pair",
    )
    RequireArch(Cursor.ReadInts("<2H"), (65534, 0), "guarded line relation flags")
    First = ReadPadHandle(Cursor)
    Second = ReadPadHandle(Cursor)
    FirstId, FirstOwner, FirstFlags = Cursor.Handles[First]
    SecondId, SecondOwner, SecondFlags = Cursor.Handles[Second]
    RequireArch(
        (FirstOwner, FirstFlags, SecondOwner, SecondFlags),
        (-1, 0, -1, 0),
        "local line pair",
    )
    LineIds = {
        LineValue["native_id"]
        for LineValue in Geometry["lines"]
        if LineValue["native_id"] >= 0
    }
    RequireArch(
        FirstId != SecondId and {FirstId, SecondId} <= LineIds,
        True,
        "distinct upper-pad line members",
    )
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "guarded line pair return")
    return PadLinePair(
        Start, Cursor.Offset, CodeValue, (First, Second), (FirstId, SecondId)
    )


# an inline upper profile reaches its contour only after the line pair branch closes
def ReadPadProfMut(Cursor: ArchiveCursor) -> tuple[ProfileSketch, PadLinePair]:
    Start = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moProfileFeature_c",), KClassRefKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId, _ = ReadProfileHead(Cursor, (0x40000000, 0xC0000000))
    SketchOffset = Cursor.Offset
    _, _, SketchIndex = Cursor.TakePointer(
        ("sgSketch",), KClassRefKind, CompactOnly=True
    )
    Local = SketchArchive(Cursor)
    Geometry, Members = ReadGeoSpansMut(Local, SketchIndex)
    PairValue = ReadPadPair(Local, Geometry)
    ReadRelationEnd(Local)
    ReadLogicalEnd(Local)
    ReadSketchEnd(Local, Geometry)
    Cursor.Offset, Cursor.NextIndex = Local.Offset, Local.NextIndex
    return (
        ProfileSketch(
            NameValue,
            FeatureId,
            ObjectIndex,
            Start,
            SketchOffset,
            SketchIndex,
            Geometry,
            [],
            Members,
        ),
        PairValue,
    )
