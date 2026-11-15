"""Read nested sketches in the equation-bearing native configuration."""

from convert.adapters.solidworks.sketch.Geometry import KAxisRelations, ReadGeometryMut as ReadGeometry
from SketchCursor import SketchCursor
from SketchPresentation import ReadPresentation
from SketchRoot import ReadSketchStart, Require


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
