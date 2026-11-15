"""Read the two supported geometry groups from the native configuration map."""

import json as Json
from pathlib import Path
from struct import unpack_from as Unpack

from DepthDisplay import read_sketch_display_close, read_sketch_display_open
from SketchCursor import SketchCursor
from SketchGeom import (
    ReadDims,
    ReadLineItem,
    ReadPointCoincidence,
    ReadPointItem,
    ReadRelations,
)
from SketchRoot import KGeneration, ReadSketchStart, Require
from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind

# the portable layout must refer to the exact normalized native pointer witness
KDisplayEvidence = "d724ad7b0c0d7daed50adf96028c08a3f83e5afde5e841ca25506cd6baf3939a"

# the native one-member relation's geometry check selects these sketch-local axes
KAxisRelations = {4: "horizontal", 5: "vertical"}

# the configuration map may allocate these names before the resolved sketch reuses them
KDisplayClasses = (
    "moDisplayDistanceDim_c",
    "moSkDimHandleValG2_c",
    "moFavoriteHandle_c",
    "moSketchRegion_c",
)


# the display layout is shared by rectangles in either archive stream
def ReadDisplayFrame(BuildName, FrameIndex):
    LayoutPath = Path(__file__).with_name("SketchDisplay.json")
    LayoutData = Json.loads(LayoutPath.read_text(encoding="utf-8"))
    Require(
        (LayoutData["generation"], LayoutData["build"], LayoutData["evidence_sha256"]),
        (KGeneration, BuildName, KDisplayEvidence),
        "verified research display layout",
    )
    return LayoutData["frames"][FrameIndex]


# resolved sketches can allocate names already present in the equivalent configuration frame
def DisplayKind(Cursor, KindValue, ClassName, Resolved):
    if (
        Resolved
        and ClassName in KDisplayClasses
        and ClassName not in Cursor.Classes.values()
    ):
        return KDefinitionKind
    return KindValue


# each saved display handle owns one slot of the same decoded sketch's dimension group
def ReadDisplaySteps(Cursor, Steps, SketchObject, DimensionLengths, *, Resolved=False):
    SlotCount = 0
    for Width, KindValue, NameValue, *Count in Steps:
        Cursor.AdvanceBytes(Width)
        Cursor.TakePointer(
            (NameValue,), DisplayKind(Cursor, KindValue, NameValue, Resolved)
        )
        if Count:
            (Value,) = Unpack("<H", Cursor.BlobValue, Cursor.Offset)
            Require(Value, Count[0], "witnessed display list count")
        if NameValue == "moDisplayDistanceDim_c":
            read_sketch_display_open(Cursor)
            HandleClass = "moSkDimHandleValG2_c"
            Cursor.TakePointer(
                (HandleClass,),
                DisplayKind(Cursor, KClassRefKind, HandleClass, Resolved),
            )
            Slot = Cursor.ReadDimHandle(SketchObject)
            Require(
                Slot == SlotCount < len(DimensionLengths),
                True,
                "ordered sketch dimension slot",
            )
            FavoriteClass = "moFavoriteHandle_c"
            FavoriteKind = (
                KClassRefKind
                if FavoriteClass in Cursor.Classes.values()
                else KDefinitionKind
            )
            read_sketch_display_close(Cursor, DimensionLengths[Slot], FavoriteKind)
            SlotCount += 1
    Require(
        SlotCount,
        len(DimensionLengths),
        "display owns the ordered sketch dimension slots",
    )


# presentation records carry pointer allocations needed to reach the next geometry group
def ReadDisplay(
    Cursor, BuildName, FrameIndex, PointIds, SketchObject, DimensionLengths
):
    Frame = ReadDisplayFrame(BuildName, FrameIndex)
    Steps = Frame["steps"]
    Coincidences = []
    if FrameIndex == 0:
        Require(
            Cursor.ReadValue("<7H"),
            tuple(Frame["inline_prefix"]),
            "inline display framing",
        )
    else:
        Coincidences.append(ReadPointCoincidence(Cursor, PointIds))
    ReadDisplaySteps(Cursor, Steps, SketchObject, DimensionLengths)
    Cursor.AdvanceBytes(Frame["trailer_width"])
    return Coincidences


# the first sketch returns inside active serializers that must finish their fields in order
def ReadRelationManagerTail(Cursor):
    Cursor.ReadValue("<i")
    Cursor.ReadRefTail()
    Cursor.ReadText()
    Cursor.ReadValue("<4i")
    Cursor.ReadEqSideTail()
    Cursor.ReadObject("moRelEquationSide_c")
    Cursor.ReadRelationTail()
    Cursor.ReadObject("moRelation_c")
    Require(Cursor.ReadValue("<H"), (0,), "empty relation manager parameter list")
    Cursor.ReadText()
    Cursor.ReadValue("<4i")
    Require(Cursor.ReadValue("<H"), (0,), "empty additional relation manager list")
    Cursor.ReadValue("<i")
    Require(Cursor.ReadValue("<i"), (0,), "empty relation manager parameter array")


# relation targets need same sketch line identity evidence before downstream comparison
def ReportRelations(Cursor, Relations, Lines):
    Records = []
    Segments = {Line[1]: Line for Line in Lines if Line[1] >= 0}
    Require(
        len(Segments), sum(Line[1] >= 0 for Line in Lines), "unique line identities"
    )
    for Start, StopValue, Target, TypeValue, Flags in Relations:
        Handle = Cursor.Handles[Target]
        Require(Handle[1:], (-1, 0), "witnessed local relation handle fields")
        Require(TypeValue in KAxisRelations, True, "supported one-member relation type")
        Segment = Segments[Handle[0]]
        Records.append(
            {
                "start": Start,
                "end": StopValue,
                "line_handle_object": Target,
                "line_handle_fields": Handle,
                "segment_native_id": Segment[1],
                "type_code": TypeValue,
                "kind": KAxisRelations[TypeValue],
                "scalar_fields": Flags,
            }
        )
    return Records


# distance parameter instances resolve their point handles within the enclosing sketch
def ReportDimensions(Cursor, Points):
    Records = []
    for ClassName, Index, NameValue, Value, First, Second in Cursor.Dimensions:
        Operands = []
        for HandleIndex in (First, Second):
            Position, Owner, Flags = Cursor.Handles[HandleIndex]
            Require((Owner, Flags), (-1, 0), "witnessed local dimension handle fields")
            Require(0 <= Position < len(Points), True, "dimension point in its sketch")
            Identity, _, _ = Points[Position]
            Operands.append((Position, Identity))
        Records.append(
            {
                "class": ClassName,
                "native_id": Index,
                "name": NameValue,
                "metres": Value,
                "point_handle_objects": [First, Second],
                "point_native_ids": Operands,
            }
        )
    return Records


# one geometry reader serves both native sketches across the supported controlled captures
def ReadGeometry(Cursor, ObjectIndex):
    Start = Cursor.Offset
    Cursor.Dimensions.clear()
    Cursor.PointReferences.clear()
    PointCount = Cursor.ReadCount()
    Points = [ReadPointItem(Cursor) for _ in range(PointCount)]
    Lines = [ReadLineItem(Cursor, PointCount) for _ in range(Cursor.ReadCount())]
    ReadDims(Cursor)
    Relations = ReadRelations(Cursor)
    return {
        "object_index": ObjectIndex,
        "body_start": Start,
        "geometry_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
        "points_metres": [Coords for _, _, Coords in Points],
        "point_relation_tallies": [
            {"id": (Position, Identity), "tally": Tally}
            for Position, (Identity, Tally, _) in enumerate(Points)
        ],
        "external_point_references": [
            {"local_id": (Position, Identity), **Cursor.PointReferences[Identity]}
            for Position, (Identity, _, _) in enumerate(Points)
            if Identity in Cursor.PointReferences
        ],
        "lines": [
            {
                "member_index": Index,
                "native_id": Identity,
                "flags": Flags,
                "point_indices": [First, Second],
            }
            for Index, Identity, Flags, First, Second in Lines
        ],
        "length_dimensions": ReportDimensions(Cursor, Points),
        "member_relations": ReportRelations(Cursor, Relations, Lines),
    }


# one cursor can finish nested sketches without losing the enclosing relation frames
def ReadSketches(BlobValue, BuildName, IncludeCoincidence=False):
    Sketches, Cursor = ReadSketchConfiguration(BlobValue, BuildName, IncludeCoincidence)
    return Sketches, {"end": Cursor.Offset, "next_map_index": Cursor.NextIndex}


# the config tail needs the allocated map as well as the measured sketch summary
def ReadSketchConfiguration(BlobValue, BuildName, IncludeCoincidence=False):
    Start = ReadSketchStart(BlobValue)
    Sketches = []

    def ReadSketchObject(Cursor, ObjectIndex):
        FrameIndex = len(Sketches)
        Require(FrameIndex < 2, True, "supported number of sketch allocations")
        Sketch = ReadGeometry(Cursor, ObjectIndex)
        PointIds = [Point["id"] for Point in Sketch["point_relation_tallies"]]
        Coincidences = ReadDisplay(
            Cursor,
            BuildName,
            FrameIndex,
            PointIds,
            ObjectIndex,
            [Dimension["metres"] for Dimension in Sketch["length_dimensions"]],
        )
        if IncludeCoincidence:
            Sketch["point_coincidences"] = Coincidences
        Sketch["body_end"] = Cursor.Offset
        Sketch["map_index_after_body"] = Cursor.NextIndex
        Sketches.append(Sketch)

    Cursor = SketchCursor(BlobValue, Start, ReadSketchObject)
    ReadSketchObject(Cursor, Cursor.NextIndex - 1)
    ReadRelationManagerTail(Cursor)
    Require(len(Sketches), 2, "both expected sketch bodies")
    return Sketches, Cursor
