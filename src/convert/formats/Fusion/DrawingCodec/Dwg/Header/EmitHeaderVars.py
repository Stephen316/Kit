from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import PutHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutTextsMut import PutTextsMut
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import (
    KHeaderFill,
    KHeaderFinish,
    KHeaderStart,
    FrameParts,
    HasHighWord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderSpec import KHeaderSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.WalkSpec import (
    CachedSpec,
    PutWalkMut,
)


def EmitHeaderVars(
    HeaderVars: DwgRecord, Frame: DwgRecord, FileHeader: DwgFileHeader
) -> bytes:
    Sinks = RecordSinks(FileHeader.VersionText)
    Writer = Sinks.DataWriter
    PutWalkMut(CachedSpec(KHeaderSpec), HeaderVars, Sinks, ())
    PutTextsMut(Writer, tuple(Sinks.TextItems), True)
    BitSize = Writer.BitCount + 32
    for Reference in Sinks.HandleRefs:
        PutHandleMut(Writer, Reference)
    TailWidth, TailBits, TrailBytes = FrameParts(Frame)
    Writer.PutBits(TailBits, TailWidth)
    Padding = -Writer.BitCount & 7
    Writer.PutBits(KHeaderFill & ((1 << Padding) - 1), Padding)
    AreaValue = PackFields("<I", BitSize) + Writer.ToBytes()
    HighWord = bytes(4) if HasHighWord(FileHeader) else b""
    Covered = PackFields("<I", len(AreaValue)) + HighWord + AreaValue
    CrcValue = PackFields("<H", CrcSixteen(0xC0C1, Covered))
    return KHeaderStart + Covered + CrcValue + KHeaderFinish + TrailBytes
