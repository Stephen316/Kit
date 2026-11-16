from convert.Formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.Formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.Formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


# the creases operation needs a distinct decoding boundary so control cage topology retains its native connectivity
def ReadCreases(Cursor: TextCursor) -> CreaseData | None:
    if not Cursor.HasKind("100edges"):
        return None
    Edges = tuple(ReadInteger(Value) for Value in Cursor.ReadFields("100edges"))
    Vertices = tuple(ReadInteger(Value) for Value in Cursor.ReadFields("100verts"))
    return CreaseData(Edges, Vertices)
