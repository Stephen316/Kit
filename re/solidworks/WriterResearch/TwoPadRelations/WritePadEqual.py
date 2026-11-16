# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the active same-length logical relation for one upper-pad sketch."""

from math import isclose as IsClose, isfinite as IsFinite
from struct import pack as PackFields
from typing import TypeAlias

from PartArchive import PartArchiveState, PartArchiveWriter
from SketchDimBase import WriteDimBase
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import EncodeNull, KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry, SketchLine

# planar directed endpoints let callers provide the actual operand locations
PadPoint: TypeAlias = tuple[float, float]

# preserving both endpoints allows the relation to check corner ownership
PadSide: TypeAlias = tuple[PadPoint, PadPoint]

# the licensed line law has no driven value or external participant
KPadEqualCode = 14


# local line slots own every coordinate used to verify the geometric roles
def ReadPadSide(Geometry: SketchGeometry, LineRow: SketchLine) -> PadSide:
    Points = Geometry["points_metres"]
    Indices = LineRow["point_indices"]
    RequireArch(
        len(Indices) == 2
        and all(type(Index) is int and 0 <= Index < len(Points) for Index in Indices),
        True,
        "two owned upper-pad endpoints",
    )
    First, Second = (Points[Index] for Index in Indices)
    RequireArch(
        len(First) == len(Second) == 2 and all(map(IsFinite, (*First, *Second))),
        True,
        "finite planar upper-pad endpoints",
    )
    return (First[0], First[1]), (Second[0], Second[1])


# four distinct orthogonal sides distinguish a closed perimeter from helper geometry
def ReadPadSides(Geometry: SketchGeometry) -> dict[int, PadSide]:
    Rows = tuple(
        LineRow
        for LineRow in Geometry["lines"]
        if LineRow["native_id"] >= 0 or LineRow["flags"] == 4
    )
    RequireArch(
        len(Rows) == 4
        and len({LineRow["member_index"] for LineRow in Rows}) == 4
        and all(
            LineRow["flags"] == 4
            and type(LineRow["native_id"]) is int
            and 0 <= LineRow["native_id"] <= 65535
            for LineRow in Rows
        ),
        True,
        "four distinct active upper-pad line members",
    )
    Sides = {LineRow["native_id"]: ReadPadSide(Geometry, LineRow) for LineRow in Rows}
    Corners = {Point for Side in Sides.values() for Point in Side}
    XValues = {Point[0] for Point in Corners}
    YValues = {Point[1] for Point in Corners}
    RequireArch(
        len(Sides) == len(Corners) == 4
        and len(XValues) == len(YValues) == 2
        and len({frozenset(Side) for Side in Sides.values()}) == 4
        and all(
            (First[0] == Second[0]) != (First[1] == Second[1])
            for First, Second in Sides.values()
        ),
        True,
        "one rectangular upper-pad perimeter",
    )
    return Sides


# explicit active axis handles join the directed perimeter to this allocated sketch
def CheckPadAxes(
    StateValue: PartArchiveState, Geometry: SketchGeometry, Sides: dict[int, PadSide]
) -> None:
    Objects = dict(StateValue.Objects)
    SketchIndex = Geometry["object_index"]
    MostRecent = max(
        (Index for Index, Name in StateValue.Objects if Name == "sgSketch"),
        default=-1,
    )
    RequireArch(
        Objects.get(SketchIndex) == "sgSketch"
        and SketchIndex == MostRecent
        and Geometry["next_map_index"] == StateValue.NextIndex
        and StateValue.NextIndex + 1 < KBigObjectTag
        and any(Name == "sgLineHandle" for _, Name in StateValue.Classes),
        True,
        "active upper-pad sketch and compact line handle class",
    )
    Axes = Geometry["member_relations"]
    RequireArch(
        len(Axes) == len({Axis["line_handle_object"] for Axis in Axes}) == 4
        and {Axis["segment_native_id"] for Axis in Axes} == Sides.keys(),
        True,
        "one active axis handle for each upper-pad perimeter line",
    )
    for Axis in Axes:
        LineId = Axis["segment_native_id"]
        Handle = Axis["line_handle_object"]
        First, Second = Sides[LineId]
        Code = 5 if First[0] == Second[0] else 4
        RequireArch(
            SketchIndex < Handle < StateValue.NextIndex
            and Objects.get(Handle) == "sgLineHandle"
            and Axis["line_handle_fields"] == (LineId, -1, 0)
            and Axis["type_code"] == Code
            and Axis["scalar_fields"] == (65534, 0),
            True,
            "axis handle owns its local directed line",
        )


# this branch admits only the witnessed ordered vertical and horizontal operands
def CheckPadEqual(Sides: dict[int, PadSide], LineIds: tuple[int, int]) -> None:
    RequireArch(
        type(LineIds) is tuple
        and len(LineIds) == 2
        and all(type(LineId) is int and LineId in Sides for LineId in LineIds)
        and LineIds[0] != LineIds[1],
        True,
        "two different owned upper-pad lines",
    )
    Vertical, Horizontal = (Sides[LineId] for LineId in LineIds)
    RiseLength = abs(Vertical[0][1] - Vertical[1][1])
    RunLength = abs(Horizontal[0][0] - Horizontal[1][0])
    RequireArch(
        Vertical[0][0] == Vertical[1][0]
        and Horizontal[0][1] == Horizontal[1][1]
        and 0 < RiseLength
        and 0 < RunLength
        and IsFinite(RiseLength)
        and IsFinite(RunLength)
        and IsClose(RiseLength, RunLength, rel_tol=1e-12),
        True,
        "adjacent equal vertical and horizontal upper-pad lines",
    )


# a fresh logical lane allocates exactly two handles before display ownership resumes
def EncodePadEqual(
    Generation: int,
    StateValue: PartArchiveState,
    Geometry: SketchGeometry,
    LineIds: tuple[int, int],
) -> tuple[bytes, PartArchiveState]:
    RequireArch(Generation, KConfigGen, "upper-pad logical relation generation")
    Sides = ReadPadSides(Geometry)
    CheckPadAxes(StateValue, Geometry, Sides)
    CheckPadEqual(Sides, LineIds)
    Writer = PartArchiveWriter(StateValue)
    Writer.u16(1)
    WriteDimBase(Writer, -1, KPadEqualCode)
    Writer.i16(-2)
    Writer.u16(0)
    for LineId in LineIds:
        Writer.BeginObject("sgLineHandle", 1)
        Writer.raw(PackFields("<H2i", LineId, -1, 0))
    Writer.raw(PackFields("<2H", 0, 0))
    NullValue = EncodeNull()
    Writer.raw(NullValue)
    Writer.raw(PackFields("<H2i2d", 0, -1, -1, 0.0, 0.0))
    Writer.raw(NullValue * 3)
    Writer.raw(PackFields("<Hi6H", 0, -1, 0, 0, 0, 0, 0, 0))
    return Writer.Build(), Writer.Snapshot()
