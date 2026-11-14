from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsInt,
    AsRecords,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.ByteCodec import (
    EmitByteSpec,
    ReadByteSpec,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import NamedValue

KAcDsHeadSpec = "; ".join(
    (
        "Bytes Signature 4; RS HeaderSize; RS HeaderFlags; RL UnknownA",
        "RL Version; RL UnknownB; RL Revision; RL SegIdxOffset; RL SegIdxUnknown",
        "RL SegIdxCount; RL SchIdxSegment; RL DatIdxSegment; RL SearchSegment",
        "RL PrvSavSegment; RL FileSize; RL UnknownC; RL FreeSpSegment",
        "RL UnknownD; Bytes Reserved 60",
    )
)
KSegmentSpec = "; ".join(
    (
        "RS Signature; Bytes SegmentName 6; RL SegmentIndex; RL UnknownA",
        "RL SegmentSize; RL UnknownB; RL Revision; RL UnknownC; RL UnknownD",
        "RL UnknownE; Bytes Marker 8",
    )
)
KAcDsHeadSize = 0x80
KBlockSize = 0x80
KSegmentHeadSize = 0x30
KSegmentMark = b"\xac\xd5"


def ReadSegment(DataValue: bytes, Offset: int, VersionText: str) -> DwgRecord:
    HeadValue = TakeSpan(DataValue, Offset, KSegmentHeadSize, "AcDs segment header")
    HeadRecord = ReadByteSpec(KSegmentSpec, HeadValue, VersionText)
    BodySize = AsInt(NamedValue(HeadRecord, "SegmentSize")) - KSegmentHeadSize
    if BodySize < 0:
        raise ValueError("DWG AcDs segment is smaller than its header")
    BodyValue = TakeSpan(
        DataValue, Offset + KSegmentHeadSize, BodySize, "AcDs segment body"
    )
    return DwgRecord(
        (
            DwgField("SegmentOffset", Offset),
            *HeadRecord.RecordFields,
            DwgField("SegmentBody", BodyValue),
        )
    )


def ReadAcDs(DataValue: bytes, VersionText: str) -> DwgRecord:
    HeadValue = TakeSpan(DataValue, 0, KAcDsHeadSize, "AcDs file header")
    HeadRecord = ReadByteSpec(KAcDsHeadSpec, HeadValue, VersionText)
    Segments: list[DwgRecord] = []
    Offset = KAcDsHeadSize
    while Offset < len(DataValue):
        if DataValue[Offset : Offset + 2] == KSegmentMark:
            Segment = ReadSegment(DataValue, Offset, VersionText)
            Segments.append(Segment)
            Offset += AsInt(NamedValue(Segment, "SegmentSize"))
        elif any(TakeSpan(DataValue, Offset, KBlockSize, "AcDs free block")):
            raise ValueError("DWG AcDs free block holds data")
        else:
            Offset += KBlockSize
    if Offset != len(DataValue):
        raise ValueError("DWG AcDs segments overrun the section data")
    return DwgRecord((*HeadRecord.RecordFields, DwgField("Segments", tuple(Segments))))


def EmitSegment(Segment: DwgRecord, VersionText: str) -> tuple[int, bytes]:
    Fields = Segment.RecordFields
    if Fields[0].FieldName != "SegmentOffset" or Fields[-1].FieldName != "SegmentBody":
        raise ValueError("DWG AcDs segment record is malformed")
    BodyValue = AsBytes(Fields[-1].FieldValue)
    HeadBytes = EmitByteSpec(KSegmentSpec, DwgRecord(Fields[1:-1]), VersionText)
    if AsInt(NamedValue(Segment, "SegmentSize")) != len(HeadBytes) + len(BodyValue):
        raise ValueError("DWG AcDs segment size does not match its body")
    return AsInt(Fields[0].FieldValue), HeadBytes + BodyValue


def EmitAcDs(Record: DwgRecord, VersionText: str) -> bytes:
    Fields = Record.RecordFields
    if not Fields or Fields[-1].FieldName != "Segments":
        raise ValueError("DWG AcDs record lacks its segment list")
    HeadRecord = DwgRecord(Fields[:-1])
    Output = bytearray(EmitByteSpec(KAcDsHeadSpec, HeadRecord, VersionText))
    for Segment in AsRecords(Fields[-1].FieldValue):
        Offset, SegmentValue = EmitSegment(Segment, VersionText)
        if Offset < len(Output):
            raise ValueError("DWG AcDs segments overlap")
        Output += bytes(Offset - len(Output)) + SegmentValue
    FileSize = AsInt(NamedValue(HeadRecord, "FileSize"))
    if FileSize < len(Output):
        raise ValueError("DWG AcDs file size is smaller than its segments")
    return bytes(Output + bytes(FileSize - len(Output)))
