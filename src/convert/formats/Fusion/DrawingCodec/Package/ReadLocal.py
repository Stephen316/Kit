from collections.abc import Callable
from struct import unpack_from as UnpackFrom
from zlib import crc32 as CrcValue

from convert.formats.Fusion.DrawingCodec.Package.CentralRow import CentralRow
from convert.formats.Fusion.DrawingCodec.Package.InflateEntry import InflateEntry
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KDescriptorFlag,
)


def ReadLocal(
    DataValue: bytes,
    RowValue: CentralRow,
    Boundary: int,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> tuple[bytes, int]:
    Offset = RowValue.Offset
    if Offset + 30 > Boundary:
        raise ValueError("Truncated Fusion drawing package local entry")
    Fields = UnpackFrom("<I5H3I2H", DataValue, Offset)
    Magic, Extract, Flags, Method, TimeValue, DateValue = Fields[:6]
    Checksum, Packed, SizeValue, NameSize, ExtraSize = Fields[6:]
    Layout = RowValue.Layout
    HasDescriptor = bool(Flags & KDescriptorFlag)
    Expected = (
        (0, 0, 0)
        if HasDescriptor
        else (RowValue.Checksum, RowValue.Packed, RowValue.Size)
    )
    Start = Offset + 30 + NameSize
    Finish = Start + RowValue.Packed
    if (
        Magic != 0x04034B50
        or (Extract, Flags, Method) != (Layout.Extract, Layout.Flags, Layout.Method)
        or (TimeValue, DateValue) != (Layout.Time, Layout.Date)
        or (Checksum, Packed, SizeValue) != Expected
        or ExtraSize
        or DataValue[Offset + 30 : Start] != RowValue.NameBytes
        or Finish > Boundary
    ):
        raise ValueError("Fusion drawing package local and central entries disagree")
    if HasDescriptor:
        TailValue = (
            UnpackFrom("<4I", DataValue, Finish) if Finish + 16 <= Boundary else ()
        )
        if TailValue != (0x08074B50, RowValue.Checksum, RowValue.Packed, RowValue.Size):
            raise ValueError("Invalid Fusion drawing package data descriptor")
        Ending = Finish + 16
    else:
        Ending = Finish
    Payload = InflateEntry(DataValue[Start:Finish], RowValue, InflateZstd)
    if len(Payload) != RowValue.Size or CrcValue(Payload) != RowValue.Checksum:
        raise ValueError("Fusion drawing package entry size or CRC mismatch")
    return Payload, Ending
