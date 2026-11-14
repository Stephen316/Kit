from dataclasses import replace as ReplaceValue
from types import MappingProxyType as ReadOnlyMap

from convert.formats.Fusion.EntityCodec.Limits import KMaxPayload, KMaxRecords
from convert.formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.formats.Fusion.SegmentCodec.BindBulkRows import BindBulkRows
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import (
    KMaxBulkBytes,
    KMinClassCode,
)
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def BindRecords(
    Records: tuple[BulkRecord, ...], Classes: tuple[MetaClass, ...]
) -> RecordScope:
    if len(Records) > KMaxRecords:
        raise ValueError("Fusion entity graph exceeds the record count limit")
    Normalized = tuple(
        ReplaceValue(
            Entry, ClassGuid=Entry.ClassGuid.upper(), BaseGuid=Entry.BaseGuid.upper()
        )
        for Entry in Classes
    )
    Registry = {
        Index: Entry.ClassGuid.upper()
        for Index, Entry in enumerate(Classes, KMinClassCode)
    }
    Expected = {Identity for Entry in Classes for Identity in Entry.OwnerIds}
    Primaries: set[int] = set()
    Entries: set[tuple[int, int]] = set()
    Continuations: dict[int, set[str]] = {}
    TotalBytes = 0
    for Record in BindBulkRows(Normalized, Records):
        KeyValue = (Record.ObjectId, Record.TypeCode)
        if (
            KeyValue in Entries
            or type(Record.Payload) is not bytes
            or len(Record.Payload) > KMaxPayload
        ):
            raise ValueError("Duplicate or oversized Fusion entity record")
        Entries.add(KeyValue)
        TotalBytes += len(Record.Payload)
        if TotalBytes > KMaxBulkBytes:
            raise ValueError("Fusion entity graph exceeds the byte limit")
        if Record.IsPrimary:
            if Record.ObjectId in Primaries:
                raise ValueError("Duplicate Fusion entity primary record")
            Primaries.add(Record.ObjectId)
        else:
            Continuations.setdefault(Record.ObjectId, set()).add(
                Registry[Record.TypeCode]
            )
    if Primaries != Expected:
        raise ValueError("Fusion entity primary records differ from metadata owners")
    return RecordScope(
        ReadOnlyMap(Registry),
        ReadOnlyMap(
            {Identity: frozenset(Values) for Identity, Values in Continuations.items()}
        ),
    )
