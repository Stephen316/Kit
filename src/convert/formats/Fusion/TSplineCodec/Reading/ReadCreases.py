from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


def ReadCreases(Cursor: TextCursor) -> CreaseData | None:
    if not Cursor.HasKind("100edges"):
        return None
    Edges = tuple(ReadInteger(Value) for Value in Cursor.ReadFields("100edges"))
    Vertices = tuple(ReadInteger(Value) for Value in Cursor.ReadFields("100verts"))
    return CreaseData(Edges, Vertices)
