from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Frame.ReadFrameMut import ReadFrameMut
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Records.RecordGroups import RecordGroups
from convert.formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.ReadGroupsMut import ReadGroupsMut
from convert.formats.Fusion.EntityCodec.Values.ReadValueMut import ReadValueMut
from convert.formats.Fusion.EntityCodec.Values.ValueQuota import ValueQuota
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


def ReadSlack(
    Record: BulkRecord, Scope: RecordScope, Catalog: EntityCatalog
) -> tuple[EntityRecord, bytes]:
    Catalog = ReplaceValue(Catalog, Quota=ValueQuota())
    Cursor = MetaCursor(Record.Payload)
    Frame = ReadFrameMut(Cursor, Record.IsPrimary, Catalog)
    Lineage = RecordGroups(Record.ObjectId, Record.TypeCode, Scope, Catalog)
    Groups = ReadGroupsMut(Cursor, Lineage, Catalog, 0, ReadValueMut)
    Value = EntityRecord(
        Record.ObjectId, Record.TypeCode, Record.IsPrimary, Frame, Groups
    )
    return Value, Record.Payload[Cursor.Offset :]


def ReadEntity(
    Record: BulkRecord, Scope: RecordScope, Catalog: EntityCatalog
) -> EntityRecord:
    Value, Slack = ReadSlack(Record, Scope, Catalog)
    if Slack:
        raise ValueError("Unexplained trailing Fusion entity payload bytes")
    return Value
