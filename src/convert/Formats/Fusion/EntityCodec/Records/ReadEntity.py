from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.EntityCodec.Frame.ReadFrameMut import ReadFrameMut
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Records.RecordGroups import RecordGroups
from convert.Formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Values.ReadGroupsMut import ReadGroupsMut
from convert.Formats.Fusion.EntityCodec.Values.ReadValueMut import ReadValueMut
from convert.Formats.Fusion.EntityCodec.Values.ValueQuota import ValueQuota
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


# the slack operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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


# the entity operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadEntity(
    Record: BulkRecord, Scope: RecordScope, Catalog: EntityCatalog
) -> EntityRecord:
    Value, Slack = ReadSlack(Record, Scope, Catalog)
    if Slack:
        raise ValueError("Unexplained trailing Fusion entity payload bytes")
    return Value
