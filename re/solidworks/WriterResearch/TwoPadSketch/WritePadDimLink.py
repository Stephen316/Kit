# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct an ordered upper-pad sketch dimension display owner."""

from math import isclose as IsClose, isfinite as IsFinite

from Display.Compose import KDisplayClass
from DisplayFavorite import KFavoriteClass
from DisplayHandle import EncodeEmptyHandle
from OriginSketch import KObjectList, KPointHandle, KSketchClass
from PartArchive import PartArchiveState, PartArchiveWriter
from RectDimDisplay import KSketchHandle
from RectangleCorners import KLineHandle
from RectangleDims import KLengthClass
from ResolvedFolders import KNameClass
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    KPointId,
    KSketchDistance,
    SketchGeometry,
)
from convert.adapters.solidworks.Sketch.Objects import KDistanceTypes

# the two length owners precede the horizontal and vertical origin offsets
KPadDimClasses = (KDistanceTypes[0], *KDistanceTypes)


# each operand must reach the local geometry slot and its saved identity
def ReadDimPoint(Geometry: SketchGeometry, PointValue: KPointId) -> tuple[float, float]:
    Index, _ = PointValue
    Points = Geometry["points_metres"]
    Tallies = Geometry["point_relation_tallies"]
    RequireArch(
        type(Index) is int
        and 0 <= Index < min(len(Points), len(Tallies))
        and Tallies[Index]["id"] == PointValue,
        True,
        "owned sketch dimension point",
    )
    Local = Points[Index]
    RequireArch(
        len(Local) == 2 and all(map(IsFinite, Local)),
        True,
        "finite planar dimension point",
    )
    return Local[0], Local[1]


# equal numeric width and height cannot identify roles without their actual endpoints
def CheckDimRoles(Geometry: SketchGeometry, Rows: list[KSketchDistance]) -> None:
    Width, Height, Left, Bottom = Rows
    RequireArch(
        tuple(DimValue["class"] for DimValue in Rows),
        KPadDimClasses,
        "ordered upper-pad dimension classes",
    )
    Anchor, WidthEnd = Width["point_native_ids"]
    HeightAnchor, HeightEnd = Height["point_native_ids"]
    Origin, LeftAnchor = Left["point_native_ids"]
    RequireArch(
        (HeightAnchor, LeftAnchor, tuple(Bottom["point_native_ids"])),
        (Anchor, Anchor, (Origin, Anchor)),
        "shared corner and origin offset operands",
    )
    AnchorX, AnchorY = ReadDimPoint(Geometry, Anchor)
    WidthX, WidthY = ReadDimPoint(Geometry, WidthEnd)
    HeightX, HeightY = ReadDimPoint(Geometry, HeightEnd)
    OriginX, OriginY = ReadDimPoint(Geometry, Origin)
    RequireArch(
        WidthY == AnchorY
        and HeightX == AnchorX
        and (OriginX, OriginY) == (0, 0)
        and any(
            RefValue["local_id"] == Origin
            and RefValue["handle_class"] == KPointHandle
            and RefValue["handle_fields"] == (0, -1, 0)
            for RefValue in Geometry["external_point_references"]
        ),
        True,
        "width height and offsets keep their owned axes and origin",
    )
    Deltas = (WidthX - AnchorX, HeightY - AnchorY, AnchorX - OriginX, AnchorY - OriginY)
    RequireArch(
        all(
            Delta > 0
            and DimValue["metres"] > 0
            and IsFinite(Delta)
            and IsClose(Delta, DimValue["metres"], rel_tol=1e-12, abs_tol=1e-14)
            for DimValue, Delta in zip(Rows, Deltas, strict=True)
        ),
        True,
        "positive distances agree with their distinct geometry roles",
    )


# the actual allocated dimension children establish ownership independently of values
def CheckDimObjects(
    Objects: dict[int, str], Geometry: SketchGeometry, Rows: list[KSketchDistance]
) -> None:
    SketchIndex = Geometry["object_index"]
    GeometryEnd = Geometry["next_map_index"]
    DimObjects = tuple(
        Index
        for Index in sorted(Objects)
        if SketchIndex < Index < GeometryEnd and Objects[Index] in KDistanceTypes
    )
    RequireArch(len(DimObjects), len(Rows), "owned sketch dimension allocations")
    NativeIds = tuple(DimValue["native_id"] for DimValue in Rows)
    RequireArch(
        len(set(NativeIds)) == 4
        and all(type(Index) is int and 0 < Index <= 0x7FFFFFFF for Index in NativeIds),
        True,
        "distinct upper-pad dimension identities",
    )
    for DimIndex, DimValue in zip(DimObjects, Rows, strict=True):
        RequireArch(
            DimIndex + 4 < GeometryEnd
            and tuple(Objects.get(Index) for Index in range(DimIndex, DimIndex + 5))
            == (DimValue["class"], KLengthClass, KNameClass, KPointHandle, KPointHandle)
            and DimValue["point_handle_objects"] == [DimIndex + 3, DimIndex + 4],
            True,
            "type and ordered point handles of the allocated local dimension",
        )


# two logical operands and prior displays give this active station a unique slot
def CheckDimStation(
    StateValue: PartArchiveState, Geometry: SketchGeometry, SlotValue: int
) -> dict[int, str]:
    Objects = dict(StateValue.Objects)
    SketchIndex = Geometry["object_index"]
    GeometryEnd = Geometry["next_map_index"]
    NextIndex = StateValue.NextIndex
    RequireArch(
        type(SlotValue) is int
        and 0 <= SlotValue < 4
        and type(SketchIndex) is int
        and type(GeometryEnd) is int
        and 0 < SketchIndex < GeometryEnd < NextIndex < KBigObjectTag
        and SketchIndex
        == max(
            (Index for Index, Name in Objects.items() if Name == KSketchClass),
            default=-1,
        )
        and {KObjectList, KSketchHandle, KDisplayClass, KFavoriteClass}
        <= {Name for Index, Name in StateValue.Classes if Index < SketchIndex},
        True,
        "active upper sketch and inherited display classes",
    )
    Expected = (
        KLineHandle,
        KLineHandle,
        KObjectList,
        *((KDisplayClass, KSketchHandle, KFavoriteClass) * SlotValue),
        KDisplayClass,
    )
    RequireArch(
        tuple(Objects.get(Index) for Index in range(GeometryEnd, NextIndex)),
        Expected,
        "ordered upper-pad display allocation station",
    )
    return Objects


# one owner record stops before annotation placement and view cache ownership
def EncodePadDimLink(
    Generation: int,
    StateValue: PartArchiveState,
    Geometry: SketchGeometry,
    SlotValue: int,
    DimensionId: int,
) -> tuple[bytes, PartArchiveState]:
    RequireArch(Generation, KConfigGen, "upper-pad display owner generation")
    Objects = CheckDimStation(StateValue, Geometry, SlotValue)
    Rows = Geometry["length_dimensions"]
    RequireArch(
        len(Rows) == 4
        and all(len(DimValue["point_native_ids"]) == 2 for DimValue in Rows)
        and type(DimensionId) is int
        and Rows[SlotValue]["native_id"] == DimensionId,
        True,
        "the requested display owns the actual ordered dimension",
    )
    CheckDimObjects(Objects, Geometry, Rows)
    CheckDimRoles(Geometry, Rows)
    Writer = PartArchiveWriter(StateValue)
    Writer.BeginObject(KSketchHandle, 1)
    Writer.raw(EncodeEmptyHandle(Generation))
    Writer.ReferenceObject(Geometry["object_index"], KSketchClass)
    Writer.i32(SlotValue)
    return Writer.Build(), Writer.Snapshot()
