from convert.formats.Fusion.TSplineCodec.Model.PlaneSymmetry import PlaneSymmetry
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.SymmetryMap import SymmetryMap
from convert.formats.Fusion.TSplineCodec.Reading.ReadPairs import ReadPairs
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber


def ReadSymmetry(Cursor: TextCursor) -> PlaneSymmetry | None:
    if not Cursor.HasKind("105sym"):
        return None
    if Cursor.ReadFields("105sym", 1) != ("0",):
        raise ValueError("Unsupported TSM symmetry mode")
    Values = tuple(ReadNumber(Value) for Value in Cursor.ReadFields("105plane", 12))
    FaceReverse = ReadPairs(Cursor, "fr")
    EdgeReverse = ReadPairs(Cursor, "er")
    VertexReverse = ReadPairs(Cursor, "vr")
    Faces = SymmetryMap(ReadPairs(Cursor, "f"), FaceReverse)
    Edges = SymmetryMap(ReadPairs(Cursor, "e"), EdgeReverse)
    Vertices = SymmetryMap(ReadPairs(Cursor, "v"), VertexReverse)
    return PlaneSymmetry(
        ControlGrip(*Values[:4]),
        ControlGrip(*Values[4:8]),
        ControlGrip(*Values[8:]),
        Faces,
        Edges,
        Vertices,
    )
