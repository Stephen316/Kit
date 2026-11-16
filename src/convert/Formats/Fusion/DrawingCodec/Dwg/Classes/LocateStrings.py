from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)


# locate strings needs an explicit validity boundary so section boundaries and object references remain consistent
def LocateStrings(DataValue: bytes, DataStart: int, EndBit: int) -> tuple[int, int]:
    if BitCursor(DataValue, EndBit - 1, EndBit).TakeBits(1) != 1:
        raise ValueError("DWG class string stream is absent")
    SizeBit = EndBit - 17
    LowWord = ReadRawShortMut(BitCursor(DataValue, SizeBit, EndBit))
    StreamSize = LowWord
    if LowWord & 0x8000:
        SizeBit -= 16
        HighWord = ReadRawShortMut(BitCursor(DataValue, SizeBit, EndBit))
        StreamSize = (LowWord & 0x7FFF) | HighWord << 15
    if StreamSize > SizeBit - DataStart:
        raise ValueError("DWG class string stream exceeds the class data")
    return SizeBit - StreamSize, SizeBit
