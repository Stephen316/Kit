from typing import cast as CastValue

from convert.formats.Fusion.DrawingCodec.Legacy.LegacyHeader import LegacyHeader
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.SegmentCodec.BindBulkRows import BindBulkRows
from convert.formats.Fusion.SegmentCodec.Bulk.EmitBulkStream import EmitBulkStream
from convert.formats.Fusion.SegmentCodec.Metadata.EmitWireRows import (
    EmitWireClasses,
    EmitWireTable,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaLimits import KMaxMetaIds
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaOffset
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink

KLegacyVersion = 2

KModernMagic = 1234


def CheckLegacyHead(Header: LegacyHeader) -> None:
    if not isinstance(CastValue(object, Header), LegacyHeader):
        raise ValueError("Expected a typed legacy Fusion drawing segment header")
    if (
        Header.Version != KLegacyVersion
        or Header.Software == KModernMagic
        or Header.RepeatedKind != Header.Kind
        or Header.StorageWords != (1, 0)
    ):
        raise ValueError("Unsupported legacy Fusion drawing segment header")


def EmitLegacy(Value: LegacySegment) -> tuple[bytes, bytes]:
    if not isinstance(CastValue(object, Value), LegacySegment):
        raise ValueError("Expected a typed legacy Fusion drawing segment")
    Header = Value.Header
    CheckLegacyHead(Header)
    BulkData, Entries = EmitBulkStream(BindBulkRows(Value.Classes, Value.Records))
    Primary = tuple(
        MetaOffset(Identity, Offset)
        for Offset, Identity, FlagValue in Entries
        if FlagValue
    )
    Others = tuple(
        MetaOffset(Identity, Offset)
        for Offset, Identity, FlagValue in Entries
        if not FlagValue
    )
    SinkValue = MetaSink()
    SinkValue.AddText(Header.Kind)
    SinkValue.AddWord(Header.SegmentId)
    SinkValue.AddText(Header.Namespace, WideText=True)
    SinkValue.AddWord(Header.Software)
    SinkValue.AddWord(Header.Version)
    SinkValue.AddText(Header.RepeatedKind)
    SinkValue.AddText(Header.StorageSpace)
    for Number in Header.StorageWords:
        SinkValue.AddWord(Number)
    EmitWireClasses(SinkValue, Value.Classes)
    SinkValue.AddCount(Value.StoredIds, KMaxMetaIds)
    for Identity in Value.StoredIds:
        SinkValue.AddLong(Identity)
    EmitWireTable(SinkValue, Primary)
    EmitWireTable(SinkValue, Others)
    SinkValue.AddLong(Value.NextId)
    return BulkData, bytes(SinkValue.Buffer)
