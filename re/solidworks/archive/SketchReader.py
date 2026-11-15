"""Read the two supported geometry groups from the native configuration map."""

import json as Json
from pathlib import Path
from struct import unpack_from as Unpack

from SketchCursor import SketchCursor, SketchEntry
from SketchGeom import ReadDims, ReadLineItem, ReadPointItem, ReadRelations
from SketchRoot import KGeneration, ReadSketchStart, Require

# the portable layout must refer to the exact normalized native pointer witness
KDisplayEvidence = "d724ad7b0c0d7daed50adf96028c08a3f83e5afde5e841ca25506cd6baf3939a"


# presentation records carry pointer allocations needed to reach the next geometry group
def ReadDisplay(Cursor, BuildName):
    LayoutPath = Path(__file__).with_name("SketchDisplay.json")
    LayoutData = Json.loads(LayoutPath.read_text(encoding="utf-8"))
    Require(
        (LayoutData["generation"], LayoutData["build"], LayoutData["evidence_sha256"]),
        (KGeneration, BuildName, KDisplayEvidence),
        "verified research display layout",
    )
    Require(Cursor.ReadValue("<7H"), (0,) * 7, "empty inline display groups")
    for Width, KindValue, NameValue, *Count in LayoutData["steps"]:
        Cursor.AdvanceBytes(Width)
        Cursor.TakePointer((NameValue,), KindValue)
        if Count:
            (Value,) = Unpack("<H", Cursor.BlobValue, Cursor.Offset)
            Require(Value, Count[0], "witnessed display list count")
    Cursor.AdvanceBytes(LayoutData["trailer_width"])


# a sketch returned within a relation must resume the owning serializers in order
def ReadNextSketch(Cursor):
    Cursor.ReadValue("<i")
    Cursor.ReadRefTail()
    Cursor.ReadText()
    Cursor.ReadValue("<4i")
    Cursor.ReadText()
    Cursor.ReadValue("<2i")
    Cursor.ReadObject("moRelation_c")
    try:
        Cursor.ReadObject("moRelEquationSide_c")
    except SketchEntry as Entry:
        return Entry.Index
    raise ValueError("Relation side did not materialize the next sketch")


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


# sharing one cursor assures the second sketch was reached by actual typed allocation
def ReadSketches(BlobValue, BuildName):
    Start = ReadSketchStart(BlobValue)
    Cursor = SketchCursor(BlobValue, Start)
    First = ReadGeometry(Cursor, Cursor.NextIndex - 1)
    ReadDisplay(Cursor, BuildName)
    First["body_end"] = Cursor.Offset
    Second = ReadGeometry(Cursor, ReadNextSketch(Cursor))
    return [First, Second]
