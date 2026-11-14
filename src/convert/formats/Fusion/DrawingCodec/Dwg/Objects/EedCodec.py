from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import (
    PutBitShortMut,
    PutHandleMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import PutBytesMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import ReadHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgEed import DwgEed
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.EedItems import (
    EncodeEedItems,
    ReadEedItems,
)


def DecodeEed(AppRef: DwgHandleRef, DataValue: bytes) -> DwgEed:
    try:
        EedItems = ReadEedItems(DataValue)
    except ValueError:
        return DwgEed(AppRef, DwgRecord(()), DataValue)
    if EncodeEedItems(EedItems) != DataValue:
        return DwgEed(AppRef, DwgRecord(()), DataValue)
    return DwgEed(AppRef, EedItems, b"")


def EncodeEed(EedBlock: DwgEed) -> bytes:
    if EedBlock.RawData:
        return EedBlock.RawData
    return EncodeEedItems(EedBlock.EedItems)


def ReadEedMut(Cursor: BitCursor) -> tuple[DwgEed, ...]:
    EedBlocks: list[DwgEed] = []
    while (EedSize := ReadBitShortMut(Cursor)) != 0:
        AppRef = ReadHandleMut(Cursor)
        DataValue = Cursor.TakeBits(8 * EedSize).to_bytes(EedSize, "big")
        EedBlocks.append(DecodeEed(AppRef, DataValue))
    return tuple(EedBlocks)


def PutEedMut(Writer: BitWriter, EedBlocks: tuple[DwgEed, ...]) -> None:
    for EedBlock in EedBlocks:
        DataValue = EncodeEed(EedBlock)
        if not DataValue:
            raise ValueError("DWG extended data block is empty")
        PutBitShortMut(Writer, len(DataValue))
        PutHandleMut(Writer, EedBlock.AppRef)
        PutBytesMut(Writer, DataValue)
    PutBitShortMut(Writer, 0)
