"""Read the two supported geometry groups from the native configuration map."""

import json as Json
from pathlib import Path
from struct import unpack_from as Unpack

from SketchCursor import SketchCursor
from SketchGeom import ReadDims, ReadLineItem, ReadPointItem, ReadRelations
from SketchRoot import KGeneration, ReadSketchStart, Require

# the portable layout must refer to the exact normalized native pointer witness
KDisplayEvidence = "d724ad7b0c0d7daed50adf96028c08a3f83e5afde5e841ca25506cd6baf3939a"


# presentation records carry pointer allocations needed to reach the next geometry group
def ReadDisplay(Cursor, BuildName, FrameIndex):
    LayoutPath = Path(__file__).with_name("SketchDisplay.json")
    LayoutData = Json.loads(LayoutPath.read_text(encoding="utf-8"))
    Require(
        (LayoutData["generation"], LayoutData["build"], LayoutData["evidence_sha256"]),
        (KGeneration, BuildName, KDisplayEvidence),
        "verified research display layout",
    )
    Frame = LayoutData["frames"][FrameIndex]
    Require(
        Cursor.ReadValue("<7H"), tuple(Frame["inline_prefix"]), "inline display framing"
    )
    for Width, KindValue, NameValue, *Count in Frame["steps"]:
        Cursor.AdvanceBytes(Width)
        Cursor.TakePointer((NameValue,), KindValue)
        if Count:
            (Value,) = Unpack("<H", Cursor.BlobValue, Cursor.Offset)
            Require(Value, Count[0], "witnessed display list count")
    Cursor.AdvanceBytes(Frame["trailer_width"])


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
    for Start, StopValue, Target, Flags in Relations:
        Handle = Cursor.Handles[Target]
        Require(Handle[1:], (-1, 0), "witnessed local relation handle fields")
        Segment = Segments[Handle[0]]
        Records.append(
            {
                "start": Start,
                "end": StopValue,
                "line_handle_object": Target,
                "line_handle_fields": Handle,
                "segment_native_id": Segment[1],
                "scalar_fields": Flags,
            }
        )
    return Records


# one geometry reader serves both native sketches across the supported controlled captures
def ReadGeometry(Cursor, ObjectIndex):
    Start = Cursor.Offset
    Cursor.Dimensions.clear()
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
        "points_metres": Points,
        "lines": [
            {
                "member_index": Index,
                "native_id": Identity,
                "flags": Flags,
                "point_indices": [First, Second],
            }
            for Index, Identity, Flags, First, Second in Lines
        ],
        "length_dimensions": [
            {
                "class": ClassName,
                "native_id": Index,
                "name": NameValue,
                "metres": Value,
                "point_handle_objects": [First, Second],
            }
            for ClassName, Index, NameValue, Value, First, Second in Cursor.Dimensions
        ],
        "member_relations": ReportRelations(Cursor, Relations, Lines),
    }


# one cursor can finish nested sketches without losing the enclosing relation frames
def ReadSketches(BlobValue, BuildName):
    Start = ReadSketchStart(BlobValue)
    Sketches = []

    def ReadSketchObject(Cursor, ObjectIndex):
        FrameIndex = len(Sketches)
        Require(FrameIndex < 2, True, "supported number of sketch allocations")
        Sketch = ReadGeometry(Cursor, ObjectIndex)
        ReadDisplay(Cursor, BuildName, FrameIndex)
        Sketch["body_end"] = Cursor.Offset
        Sketch["map_index_after_body"] = Cursor.NextIndex
        Sketches.append(Sketch)

    Cursor = SketchCursor(BlobValue, Start, ReadSketchObject)
    ReadSketchObject(Cursor, Cursor.NextIndex - 1)
    ReadRelationManagerTail(Cursor)
    Require(len(Sketches), 2, "both expected sketch bodies")
    return Sketches, {"end": Cursor.Offset, "next_map_index": Cursor.NextIndex}
