from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitLongMut import ReadBitLongMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitMut import ReadBitMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadUnicodeMut import ReadUnicodeMut
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


# the class row operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadClassRowMut(MainCursor: BitCursor, TextCursor: BitCursor) -> DwgClassRow:
    ClassNumber = ReadBitShortMut(MainCursor)
    ProxyFlags = ReadBitShortMut(MainCursor)
    AppName = ReadUnicodeMut(TextCursor)
    CppName = ReadUnicodeMut(TextCursor)
    DxfName = ReadUnicodeMut(TextCursor)
    WasZombie = ReadBitMut(MainCursor) == 1
    ItemClassId = ReadBitShortMut(MainCursor)
    return DwgClassRow(
        ClassNumber=ClassNumber,
        ProxyFlags=ProxyFlags,
        AppName=AppName,
        CppName=CppName,
        DxfName=DxfName,
        WasZombie=WasZombie,
        ItemClassId=ItemClassId,
        InstanceCount=ReadBitLongMut(MainCursor),
        DwgVersion=ReadBitLongMut(MainCursor),
        MaintVersion=ReadBitLongMut(MainCursor),
        ReservedFirst=ReadBitLongMut(MainCursor),
        ReservedSecond=ReadBitLongMut(MainCursor),
    )
