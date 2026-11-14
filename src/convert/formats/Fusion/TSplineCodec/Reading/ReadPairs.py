from convert.formats.Fusion.TSplineCodec.Model.IndexPair import IndexPair
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


def ReadPairs(Cursor: TextCursor, Selector: str) -> tuple[IndexPair, ...]:
    Fields = Cursor.ReadFields("105a")
    if not Fields or Fields[0] != Selector or len(Fields) % 2 != 1:
        raise ValueError("Unsupported TSM symmetry correspondence")
    Values = tuple(ReadInteger(Value) for Value in Fields[1:])
    return tuple(
        IndexPair(Values[Index], Values[Index + 1])
        for Index in range(0, len(Values), 2)
    )
