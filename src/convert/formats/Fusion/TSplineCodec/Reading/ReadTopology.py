from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Model.CageEdge import CageEdge
from convert.formats.Fusion.TSplineCodec.Model.CageVertex import CageVertex
from convert.formats.Fusion.TSplineCodec.Model.CageLink import CageLink
from convert.formats.Fusion.TSplineCodec.Model.EndCondition import EndCondition
from convert.formats.Fusion.TSplineCodec.Reading.ReadFace import ReadFace
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadRows import ReadRows
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber


def ReadTopology(Cursor: TextCursor) -> CageTopology:
    Faces = tuple(ReadFace(Fields) for Fields in ReadRows(Cursor, "f", 2))
    Edges = tuple(
        CageEdge(ReadInteger(Fields[0]), ReadNumber(Fields[1]))
        for Fields in ReadRows(Cursor, "e", 2)
    )
    Vertices = tuple(
        CageVertex(ReadInteger(Fields[0]), Fields[1])
        for Fields in ReadRows(Cursor, "v", 2)
    )
    Links = tuple(
        CageLink(*(ReadInteger(Field) for Field in Fields))
        for Fields in ReadRows(Cursor, "l", 7)
    )
    Conditions = tuple(
        EndCondition(ReadInteger(Fields[0]), ReadNumber(Fields[1]))
        for Fields in ReadRows(Cursor, "ec", 2)
    )
    return CageTopology(Faces, Edges, Vertices, Links, Conditions)
