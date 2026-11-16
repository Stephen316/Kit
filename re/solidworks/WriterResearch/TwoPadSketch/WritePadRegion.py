# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the upper-pad sketch region and its guarded return."""

from struct import pack as PackFields

from OriginSketch import KObjectList, KSketchClass
from PartArchive import PartArchiveState, PartArchiveWriter
from RectangleCorners import KLineHandle
from RectangleRegion import CheckRectOutline, KRegionClass
from TwoPadRelations.WritePadEqual import CheckPadAxes, ReadPadSides
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry


# later presentation allocations cannot change which sketch owns the earlier geometry
def CheckRegionMap(
    StateValue: PartArchiveState, Geometry: SketchGeometry
) -> PartArchiveState:
    SketchIndex = Geometry["object_index"]
    GeometryEnd = Geometry["next_map_index"]
    PriorSketch = max(
        (Index for Index, Name in StateValue.Objects if Name == KSketchClass),
        default=-1,
    )
    PriorRegion = max(
        (Index for Index, Name in StateValue.Objects if Name == KRegionClass),
        default=-1,
    )
    Inherited = {Name for Index, Name in StateValue.Classes if Index < SketchIndex}
    RequireArch(
        type(SketchIndex) is int
        and type(GeometryEnd) is int
        and SketchIndex == PriorSketch
        and 0 < PriorRegion < SketchIndex < GeometryEnd <= StateValue.NextIndex
        and StateValue.NextIndex + 6 < KBigObjectTag
        and {KObjectList, KLineHandle, KRegionClass} <= Inherited,
        True,
        "active upper sketch and inherited lower region classes",
    )
    return PartArchiveState(
        GeometryEnd,
        tuple(
            (Index, Name) for Index, Name in StateValue.Classes if Index < GeometryEnd
        ),
        tuple(
            (Index, Name) for Index, Name in StateValue.Objects if Index < GeometryEnd
        ),
    )


# the output contains one inherited contour and closes the active inline sketch
def EncodePadRegion(
    Generation: int,
    StateValue: PartArchiveState,
    Geometry: SketchGeometry,
    Outline: tuple[int, ...],
) -> tuple[bytes, PartArchiveState]:
    RequireArch(Generation, KConfigGen, "upper-pad sketch region generation")
    GeometryState = CheckRegionMap(StateValue, Geometry)
    Sides = ReadPadSides(Geometry)
    CheckPadAxes(GeometryState, Geometry, Sides)
    Edges = {
        Line["native_id"]: (Line["point_indices"][0], Line["point_indices"][1])
        for Line in Geometry["lines"]
        if Line["native_id"] in Sides
    }
    RequireArch(
        type(Outline) is tuple and all(type(LineId) is int for LineId in Outline),
        True,
        "directed upper-pad perimeter identities",
    )
    CheckRectOutline(Edges, Outline)
    Writer = PartArchiveWriter(StateValue)
    Writer.BeginObject(KObjectList, 1)
    Writer.u16(1)
    Writer.BeginObject(KRegionClass, 1)
    Writer.BeginObject(KObjectList, 1)
    Writer.u16(len(Outline))
    for LineId in Outline:
        Writer.BeginObject(KLineHandle, 1)
        Writer.raw(PackFields("<H2i", LineId, -1, 0))
    Writer.raw(PackFields("<H7i", *(0,) * 8))
    return Writer.Build(), Writer.Snapshot()
