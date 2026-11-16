from convert.Formats.Fusion.DrawingCodec.Dwg.Inflate.ReadZeroRun import ReadZeroRun
from convert.Formats.Fusion.DrawingCodec.Dwg.Inflate.TakeByte import TakeByte


# the extended operation needs a distinct decoding boundary so compressed page boundaries cannot overrun their declared payload
def ReadExtended(Packed: bytes, Position: int) -> tuple[int, int]:
    Value = TakeByte(Packed, Position)
    if Value != 0:
        return Value, Position + 1
    RunTotal, Cursor = ReadZeroRun(Packed, Position + 1)
    return RunTotal + 0xFF, Cursor
