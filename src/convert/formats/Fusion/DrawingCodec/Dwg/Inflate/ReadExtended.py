from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.ReadZeroRun import ReadZeroRun
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte


def ReadExtended(Packed: bytes, Position: int) -> tuple[int, int]:
    Value = TakeByte(Packed, Position)
    if Value != 0:
        return Value, Position + 1
    RunTotal, Cursor = ReadZeroRun(Packed, Position + 1)
    return RunTotal + 0xFF, Cursor
