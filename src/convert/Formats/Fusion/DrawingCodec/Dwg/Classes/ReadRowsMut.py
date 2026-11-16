from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Classes.ReadClassRowMut import (
    ReadClassRowMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


# the rows operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadRowsMut(
    MainCursor: BitCursor, TextCursor: BitCursor
) -> tuple[DwgClassRow, ...]:
    ClassRows: list[DwgClassRow] = []
    while MainCursor.Position < MainCursor.Limit:
        ClassRows.append(ReadClassRowMut(MainCursor, TextCursor))
    if TextCursor.Position != TextCursor.Limit:
        raise ValueError("DWG class string stream was not fully consumed")
    return tuple(ClassRows)
