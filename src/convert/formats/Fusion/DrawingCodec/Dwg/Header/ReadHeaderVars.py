from struct import error as StructError

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import ReadHandleMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadUnicodeMut import ReadUnicodeMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Classes.LocateStrings import (
    LocateStrings,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.EmitHeaderVars import (
    EmitHeaderVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import (
    KHeaderFinish,
    KHeaderName,
    KHeaderStart,
    HasHighWord,
    MakeFrame,
    RefWidth,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderSpec import KHeaderSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordStreams import (
    RecordStreams,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.WalkSpec import (
    CachedSpec,
    ReadWalk,
)


def LocateArea(DataValue: bytes, FileHeader: DwgFileHeader) -> tuple[int, int]:
    if TakeSpan(DataValue, 0, 16, "header start sentinel") != KHeaderStart:
        raise ValueError("DWG header variables start sentinel mismatch")
    DataStart = 24 if HasHighWord(FileHeader) else 20
    AreaFinish = DataStart + ReadFields(DataValue, 16, "<I", "header size")[0]
    if DataStart == 24 and ReadFields(DataValue, 20, "<I", "header high size")[0]:
        raise ValueError("DWG header variables size exceeds 32 bits")
    CrcValue = ReadFields(DataValue, AreaFinish, "<H", "header CRC")[0]
    if CrcSixteen(0xC0C1, DataValue[16:AreaFinish]) != CrcValue:
        raise ValueError("DWG header variables CRC mismatch")
    Finish = TakeSpan(DataValue, AreaFinish + 2, 16, "header end sentinel")
    if Finish != KHeaderFinish:
        raise ValueError("DWG header variables end sentinel mismatch")
    return DataStart, AreaFinish


def ReadTexts(DataValue: bytes, TextStart: int, TextFinish: int) -> tuple[str, ...]:
    Cursor = BitCursor(DataValue, TextStart, TextFinish)
    TextItems: list[str] = []
    while Cursor.Position < TextFinish:
        TextItems.append(ReadUnicodeMut(Cursor))
    return tuple(TextItems)


def ReadRefs(
    DataValue: bytes, RefStart: int, RefFinish: int
) -> tuple[DwgHandleRef, ...]:
    Cursor = BitCursor(DataValue, RefStart, RefFinish)
    HandleRefs: list[DwgHandleRef] = []
    while RefFinish - Cursor.Position >= 8:
        try:
            HandleRefs.append(ReadHandleMut(Cursor))
        except ValueError:
            break
    return tuple(HandleRefs)


def ReadHeaderVars(
    DataValue: bytes, FileHeader: DwgFileHeader
) -> tuple[DwgRecord, DwgRecord]:
    DataStart, AreaFinish = LocateArea(DataValue, FileHeader)
    BitSize = ReadFields(DataValue, DataStart, "<I", "header bit size")[0]
    EndBit = DataStart * 8 + BitSize
    if not (32 < BitSize and EndBit <= AreaFinish * 8):
        raise ValueError("DWG header variables bit size is out of range")
    TextStart, TextFinish = LocateStrings(DataValue, DataStart * 8 + 32, EndBit)
    TextItems = ReadTexts(DataValue, TextStart, TextFinish)
    HandleRefs = ReadRefs(DataValue, EndBit, AreaFinish * 8)
    Cursor = BitCursor(DataValue, DataStart * 8 + 32, TextStart)
    Streams = RecordStreams(Cursor, TextItems, HandleRefs, FileHeader.VersionText)
    HeaderVars = ReadWalk(CachedSpec(KHeaderSpec), Streams, ())
    if Cursor.Position != TextStart or Streams.TextIndex != len(TextItems):
        raise ValueError("DWG header variables leave data or strings unread")
    UsedRefs = HandleRefs[: Streams.HandleIndex]
    TailStart = EndBit + sum(RefWidth(Reference) for Reference in UsedRefs)
    TailWidth = AreaFinish * 8 - TailStart
    TailBits = BitCursor(DataValue, TailStart, AreaFinish * 8).TakeBits(TailWidth)
    Frame = MakeFrame(TailWidth, TailBits, DataValue[AreaFinish + 18 :])
    return HeaderVars, Frame


def TypeHeader(
    DataValue: bytes | None, FileHeader: DwgFileHeader
) -> tuple[DwgRecord, tuple[tuple[str, DwgRecord], ...]]:
    Empty = DwgRecord(())
    if DataValue is None:
        return Empty, ()
    try:
        HeaderVars, Frame = ReadHeaderVars(DataValue, FileHeader)
        IsExact = EmitHeaderVars(HeaderVars, Frame, FileHeader) == DataValue
    except (ValueError, StructError):
        return Empty, ()
    if not IsExact:
        return Empty, ()
    return HeaderVars, ((KHeaderName, Frame),)
