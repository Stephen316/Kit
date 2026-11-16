from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Parameters.NumberBinding import NumberBinding


# the number binding operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadNumBinding(Payload: bytes) -> NumberBinding:
    Cursor = MetaCursor(Payload)
    if Cursor.TakeBytes(9) != bytes(4) + b"\1\1\0\0\0":
        raise ValueError("Unsupported Fusion numeric binding header")
    OwnerId = ReadNativeRef(Cursor)
    ObserverIndex = int(UnpackValue("<i", Cursor.TakeBytes(4))[0])
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion numeric binding slot")
    Number = float(UnpackValue("<d", Cursor.TakeBytes(8))[0])
    ParamId = ReadNativeRef(Cursor)
    RuntimeParamId = Cursor.ReadLong()
    if ReadNativeRef(Cursor) != OwnerId or Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Invalid Fusion numeric binding owner")
    BookId = ReadNativeRef(Cursor)
    if (
        Cursor.TakeBytes(1) != bytes(1)
        or ReadNativeRef(Cursor) != OwnerId
        or Cursor.Offset != len(Payload)
        or not IsFinite(Number)
        or ObserverIndex < -1
        or RuntimeParamId == 0
        or 0 in (OwnerId, ParamId, BookId)
        or len({OwnerId, ParamId, BookId}) != 3
    ):
        raise ValueError("Invalid Fusion numeric binding fields")
    return NumberBinding(
        OwnerId, ParamId, BookId, ObserverIndex, RuntimeParamId, Number
    )
