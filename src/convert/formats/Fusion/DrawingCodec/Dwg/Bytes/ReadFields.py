from struct import calcsize as CalcSize
from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan


# the fields operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadFields(
    DataValue: bytes, Offset: int, Layout: str, Label: str
) -> tuple[int, ...]:
    SpanValue = TakeSpan(DataValue, Offset, CalcSize(Layout), Label)
    return tuple(int(FieldValue) for FieldValue in UnpackFrom(Layout, SpanValue))
