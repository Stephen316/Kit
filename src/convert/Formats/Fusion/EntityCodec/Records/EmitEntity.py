from dataclasses import replace as ReplaceValue

from convert.Formats.Fusion.EntityCodec.Frame.EmitFrameMut import EmitFrameMut
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Records.RecordGroups import RecordGroups
from convert.Formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Values.EmitGroupsMut import EmitGroupsMut
from convert.Formats.Fusion.EntityCodec.Values.EmitValueMut import EmitValueMut
from convert.Formats.Fusion.EntityCodec.Values.ValueQuota import ValueQuota
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the entity operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitEntity(
    Record: EntityRecord, Scope: RecordScope, Catalog: EntityCatalog
) -> BulkRecord:
    Catalog = ReplaceValue(Catalog, Quota=ValueQuota())
    Output = FeatureSink()
    Output.AddBytes(EmitFrameMut(Record.Frame, Record.IsPrimary, Catalog))
    Groups = RecordGroups(Record.ObjectId, Record.TypeCode, Scope, Catalog)
    Output.AddBytes(EmitGroupsMut(Record.Groups, Groups, Catalog, 0, EmitValueMut))
    return BulkRecord(
        Record.TypeCode, Record.ObjectId, Record.IsPrimary, bytes(Output.Buffer)
    )
