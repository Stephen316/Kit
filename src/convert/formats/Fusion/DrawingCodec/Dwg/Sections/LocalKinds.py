from collections.abc import Callable

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import PutHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import (
    PutBytesMut,
    PutRawLongMut,
    PutRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import ReadHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawLongMut import ReadRawLongMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsHandle,
    AsInt,
    AsText,
)


def TakeEncoded(Cursor: BitCursor, ByteCount: int) -> str:
    if ByteCount * 8 > Cursor.Limit - Cursor.Position:
        raise ValueError("DWG section text exceeds the section data")
    Encoded = Cursor.TakeBits(ByteCount * 8).to_bytes(ByteCount, "big")
    try:
        return Encoded.decode("utf-16-le")
    except UnicodeDecodeError as ErrorInfo:
        raise ValueError("DWG section text is not valid UTF-16") from ErrorInfo


def ReadWideMut(Cursor: BitCursor) -> str:
    TextValue = TakeEncoded(Cursor, 2 * ReadRawShortMut(Cursor))
    if not TextValue.endswith("\x00"):
        raise ValueError("DWG section wide text lacks its terminator")
    return TextValue[:-1]


def PutWideMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Encoded = (AsText(Value) + "\x00").encode("utf-16-le")
    PutRawShortMut(Writer, len(Encoded) // 2)
    PutBytesMut(Writer, Encoded)


def ReadSizedMut(Cursor: BitCursor) -> str:
    ByteCount = ReadRawLongMut(Cursor)
    if ByteCount % 2:
        raise ValueError("DWG section sized text has an odd byte count")
    return TakeEncoded(Cursor, ByteCount)


def PutSizedMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Encoded = AsText(Value).encode("utf-16-le")
    PutRawLongMut(Writer, len(Encoded))
    PutBytesMut(Writer, Encoded)


def ReadQuadMut(Cursor: BitCursor) -> int:
    LowWord = ReadRawLongMut(Cursor)
    return LowWord | ReadRawLongMut(Cursor) << 32


def PutQuadMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Number = AsInt(Value)
    PutRawLongMut(Writer, Number & 0xFFFFFFFF)
    PutRawLongMut(Writer, Number >> 32)


def PutDataRefMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutHandleMut(Writer, AsHandle(Value))


KLocalReads: dict[str, Callable[[BitCursor], KDwgValue]] = {
    "HD": ReadHandleMut,
    "WT": ReadWideMut,
    "ST": ReadSizedMut,
    "RLL": ReadQuadMut,
}
KLocalPuts: dict[str, Callable[[BitWriter, KDwgValue], None]] = {
    "HD": PutDataRefMut,
    "WT": PutWideMut,
    "ST": PutSizedMut,
    "RLL": PutQuadMut,
}
