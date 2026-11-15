"""Read the two supported geometry groups from the native configuration map."""

from SketchCursor import SketchCursor
from SketchGeom import ReadDims, ReadLineItem, ReadPointItem, ReadRelations
from SketchPresentation import ReadPresentation
from SketchRoot import ReadSketchStart, Require

# the native one-member relation's geometry check selects these sketch-local axes
KAxisRelations = {4: "horizontal", 5: "vertical"}


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
        Coincidences = ReadPresentation(Cursor, BuildName, Sketch)
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
