from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Classes.ReadClassRowMut import (
    ReadClassRowMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


def ReadRowsMut(
    MainCursor: BitCursor, TextCursor: BitCursor
) -> tuple[DwgClassRow, ...]:
    ClassRows: list[DwgClassRow] = []
    while MainCursor.Position < MainCursor.Limit:
        ClassRows.append(ReadClassRowMut(MainCursor, TextCursor))
    if TextCursor.Position != TextCursor.Limit:
        raise ValueError("DWG class string stream was not fully consumed")
    return tuple(ClassRows)
