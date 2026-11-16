# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as Distance, isclose as IsClose

from typing_extensions import override as Override

from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Resolved.OriginProfile import OriginProfile
from convert.adapters.solidworks.Sketch.CircularRecords import (
    RoundDiameter,
    CircularMember,
    CircularOrigin,
    CircularPoint,
    RadialPrefix,
)
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimFields import ReadDimFields
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayBase
from convert.adapters.solidworks.Sketch.Displays import TakeShownClass
from convert.adapters.solidworks.Sketch.Members import (
    ReadMember,
    ReadPointMut,
    ReadPointSlot,
)
from convert.adapters.solidworks.Sketch.Relations import ReadRelations
from convert.adapters.solidworks.Sketch.SketchTail import ReadLogicalTail
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the full circle and the primary point adjacency share this allocated handle type
KCircleHandle = "sgArcHandle"


# this reader verifies the radialcursor boundary
class CircularCursor(SketchArchive):
    """Limit otherwise shared point adjacency to a witnessed circular handle."""

    # redirect ordinary point adjacency to the reached arc handle
    @Override
    def ReadObject(self, *Expected: str | None) -> int:
        if Expected == (None, "sgLineHandle"):
            Expected = (None, KCircleHandle)
        return super().ReadObject(*Expected)

    # decode circular adjacency and the inactive entity inactive operand
    @Override
    def ReadPayload(self, NameValue: str, ObjectIndex: int) -> None:
        if NameValue == KCircleHandle:
            (SlotValue,) = self.ReadInts("<H")
            RequireArch(
                SlotValue < 0x777F, True, "unsupported circular handle index width"
            )
            Owner, Flags = self.ReadInts("<2i")
        elif NameValue == "sgEntHandle":
            RequireArch(
                self.ReadInts("<H") == (0x777F,),
                True,
                "expected invalid placeholder index width",
            )
            SlotValue, Owner, Flags = self.ReadInts("<3i")
            RequireArch(SlotValue == -2, True, "unexpected second G1 operand")
        else:
            super().ReadPayload(NameValue, ObjectIndex)
            return
        RequireArch((Owner, Flags) == (-1, 0), True, "circular handle is not local")
        self.Handles[ObjectIndex] = SlotValue, Owner, Flags


# this reader verifies the points boundary
def ReadPoints(Cursor: CircularCursor) -> list[CircularPoint]:
    RequireArch(
        Cursor.ReadCount() == 3, True, "expected center, seam and origin-proxy points"
    )
    Points: list[CircularPoint] = []
    for SlotValue in range(3):
        StartOffset = Cursor.Offset
        Earlier = set(Cursor.Handles)
        Identity, References, Coords = ReadPointMut(Cursor)
        Adjacency = [
            Handle
            for Handle in Cursor.Handles.keys() - Earlier
            if Cursor.Objects[Handle] == KCircleHandle
        ]
        Points.append(
            {
                "slot": SlotValue,
                "id": Identity,
                "span": [StartOffset, Cursor.Offset],
                "references": References,
                "xy_m": Coords,
                "arc_adjacency": sorted(Adjacency),
            }
        )
    RequireArch(
        len({Record["id"] for Record in Points}) == len(Points),
        True,
        "duplicate source point identity",
    )
    return Points


# this reader verifies the circle boundary
def ReadCircle(Cursor: CircularCursor, Points: list[CircularPoint]) -> CircularMember:
    RequireArch(
        Cursor.ReadInts("<4i") == (0, 0, 0, 1),
        True,
        "expected one arc and no other primary members",
    )
    StartOffset = Cursor.Offset
    RequireArch(Cursor.ReadInts("<H") == (0,), True, "unsupported circular member mode")
    _, Identity, Flags, FlagsTwo, References, External = ReadMember(Cursor)
    SeamSlot, EndOffset = ReadPointSlot(Cursor), ReadPointSlot(Cursor)
    RequireArch(
        Cursor.ReadInts("<2H") == (1, 0), True, "unsupported circular endpoint fields"
    )
    RequireArch(Cursor.ReadPoint(1) == (-1,), True, "unsupported arc tolerance state")
    (Orientation,) = Cursor.ReadInts("<i")
    Center = ReadPointSlot(Cursor)
    RequireArch(
        Cursor.ReadInts("<4i") == (-2,) * 4,
        True,
        "unsupported arc auxiliary references",
    )
    RequireArch(
        (Flags, FlagsTwo, References, External, Orientation) == (4, 0, 1, 0, 1)
        and SeamSlot == EndOffset
        and SeamSlot != Center
        and {SeamSlot, Center} <= set(range(len(Points))),
        True,
        "expected one ordinary positive full circle",
    )
    Adjacency = Points[SeamSlot]["arc_adjacency"]
    RequireArch(
        len(Adjacency) == 1
        and Cursor.Handles[Adjacency[0]] == (0, -1, 0)
        and all(
            not Point["arc_adjacency"] for Point in Points if Point["slot"] != SeamSlot
        ),
        True,
        "the seam does not own the local circular adjacency",
    )
    Radius = Distance(Points[SeamSlot]["xy_m"], Points[Center]["xy_m"])
    RequireArch(Radius > 0, True, "circle center and seam coincide")
    return {
        "span": [StartOffset, Cursor.Offset],
        "arc_slot": 0,
        "native_id": Identity,
        "seam_slot": SeamSlot,
        "center_slot": Center,
        "orientation": Orientation,
        "radial_metres": Radius,
        "adjacency_handle": Adjacency[0],
    }


# this reader verifies the diameter boundary
def ReadDiameter(Cursor: CircularCursor, Circle: CircularMember) -> RoundDiameter:
    RequireArch(
        Cursor.ReadInts("<8i") == (0,) * 8, True, "unexpected remaining geometry groups"
    )
    RequireArch(Cursor.ReadInts("<H") == (1,), True, "expected one radial G1 value")
    StartOffset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(("sgCircleDim",))
    DimId, Scalar, StateValue = ReadDimFields(Cursor, "moLengthParameter_c")
    RequireArch(
        StateValue == 0 and Cursor.ReadInts("<i4H") == (15, 2, 0, 0, 0),
        True,
        "unsupported G1 diameter state",
    )
    ArcHandle = Cursor.ReadObject(KCircleHandle)
    Placeholder = Cursor.ReadObject("sgEntHandle")
    RequireArch(
        Cursor.Handles[ArcHandle] == (Circle["arc_slot"], -1, 0)
        and Cursor.Handles[Placeholder] == (-2, -1, 0),
        True,
        "the active diameter does not bind its one circular operand",
    )
    RequireArch(
        Cursor.ReadInts("<2i") == (0, 0) and Cursor.ReadPoint(3) == (1, 0, 0),
        True,
        "unsupported radial value return",
    )
    NameValue, Value = Cursor.Scalars[Scalar]
    RequireArch(
        IsClose(Value, 2 * Circle["radial_metres"], rel_tol=0, abs_tol=1e-9),
        True,
        "radial value and geometry disagree",
    )
    return {
        "span": [StartOffset, Cursor.Offset],
        "native_id": DimId,
        "object": ObjectIndex,
        "parameter_object": Scalar,
        "parameter_offset": Cursor.ScalarOffsets[Scalar],
        "parameter_name": NameValue,
        "diameter_m": Value,
        "arc_handle": ArcHandle,
        "invalid_second_handle": Placeholder,
    }


# this reader verifies the origin join boundary
def ReadOriginJoin(
    Cursor: CircularCursor,
    Points: list[CircularPoint],
    Circle: CircularMember,
    Origin: OriginProfile,
) -> CircularOrigin:
    RequireArch(
        Cursor.ReadInts("<H") == (0,) and not ReadRelations(Cursor),
        True,
        "unexpected other value or logical dimensions",
    )
    (Coincident,) = ReadLogicalTail(
        Cursor, [(Record["slot"], Record["id"]) for Record in Points]
    )
    Center = Circle["center_slot"]
    (Proxy,) = set(range(len(Points))) - {Center, Circle["seam_slot"]}
    Reference = Cursor.PointReferences.get(Points[Proxy]["id"])
    if Reference is None:
        raise ArchiveError(
            "active G2 does not join the actual circle center to the typed Origin point"
        )
    RequireArch(
        not Coincident["deleted"]
        and not Coincident["suppressed"]
        and set(Coincident["point_indices"]) == {Center, Proxy}
        and set(Cursor.PointReferences) == {Points[Proxy]["id"]}
        and Reference["feature_id"] == Origin.FeatureId
        and Reference["handle_class"] == "sgPointHandle"
        and Reference["handle_fields"] == (0, -1, 0)
        and Points[Center]["xy_m"]
        == Points[Proxy]["xy_m"]
        == Origin.Geometry.PointValue,
        True,
        "active G2 does not join the actual circle center to the typed Origin point",
    )
    return {**Coincident, "origin_feature": Origin.FeatureId, "origin_proxy": Reference}


# this reader verifies the display prefix boundary
def ReadViewPrefix(Cursor: CircularCursor) -> RadialPrefix:
    StartOffset = Cursor.Offset
    TakeShownClass(Cursor, "suObList")
    RequireArch(Cursor.ReadInts("<H") == (1,), True, "expected one radial display")
    DisplayStart = Cursor.Offset
    _, _, Display = Cursor.TakePointer(("moDisplayRadialDim_c",))
    ReadDisplayBase(Cursor, True)
    return {
        "list_start": StartOffset,
        "display_start": DisplayStart,
        "display_object": Display,
        "common_prefix_end": Cursor.Offset,
    }
