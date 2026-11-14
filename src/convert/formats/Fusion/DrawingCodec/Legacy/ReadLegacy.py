from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.DrawingCodec.Legacy.EmitLegacy import (
    CheckLegacyHead,
    EmitLegacy,
)
from convert.formats.Fusion.DrawingCodec.Legacy.LegacyHeader import LegacyHeader
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import (
    KMaxMetaIds,
    KMaxMetaSize,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.ReadWireRows import (
    ReadWireClasses,
    ReadWireTable,
)


def ReadLegacy(MetaData: bytes, BulkData: bytes) -> LegacySegment:
    if type(MetaData) is not bytes or not 0 < len(MetaData) <= KMaxMetaSize:
        raise ValueError("Invalid legacy Fusion drawing MetaStream")
    Cursor = MetaCursor(MetaData)
    Header = LegacyHeader(
        Cursor.ReadText(),
        Cursor.ReadWord(),
        Cursor.ReadText(True),
        Cursor.ReadWord(),
        Cursor.ReadWord(),
        Cursor.ReadText(),
        Cursor.ReadText(),
        (Cursor.ReadWord(), Cursor.ReadWord()),
    )
    CheckLegacyHead(Header)
    Classes = ReadWireClasses(Cursor)
    StoredIds = tuple(Cursor.ReadLong() for _ in range(Cursor.ReadCount(KMaxMetaIds)))
    Primary, Others = ReadWireTable(Cursor), ReadWireTable(Cursor)
    NextId = Cursor.ReadLong()
    if Cursor.Offset != len(MetaData):
        raise ValueError("Trailing legacy Fusion drawing MetaStream data")
    Records = SplitRecords(BulkData, Primary, Others)
    Result = LegacySegment(Header, Classes, StoredIds, NextId, Records)
    if EmitLegacy(Result) != (BulkData, MetaData):
        raise ValueError("Legacy Fusion drawing segment is not canonical")
    return Result


def SplitRecords(
    BulkData: bytes, Primary: tuple[MetaOffset, ...], Others: tuple[MetaOffset, ...]
) -> tuple[BulkRecord, ...]:
    Entries = sorted(
        [(RowValue.Offset, RowValue.ObjectId, True) for RowValue in Primary]
        + [(RowValue.Offset, RowValue.ObjectId, False) for RowValue in Others]
    )
    if not Entries or Entries[0][0] != 0:
        raise ValueError("Missing initial legacy Fusion drawing record")
    Records: list[BulkRecord] = []
    for Index, (Start, Identity, IsPrimary) in enumerate(Entries):
        Finish = Entries[Index + 1][0] if Index + 1 < len(Entries) else len(BulkData)
        if not Start + 4 <= Finish <= len(BulkData):
            raise ValueError("Invalid legacy Fusion drawing record extent")
        Length = int(UnpackFrom("<I", BulkData, Start)[0])
        Payload = Start + 12 + Length
        CodeBytes = BulkData[Start + 4 : Payload - 8]
        if not 1 <= Length <= 8 or Payload > Finish or not CodeBytes.isdigit():
            raise ValueError("Invalid legacy Fusion drawing record header")
        if int(UnpackFrom("<Q", BulkData, Payload - 8)[0]) != Identity:
            raise ValueError("Legacy Fusion drawing record identity disagrees")
        Records.append(
            BulkRecord(int(CodeBytes), Identity, IsPrimary, BulkData[Payload:Finish])
        )
    return tuple(Records)
