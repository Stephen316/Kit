from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Frame.EmitFrameMut import EmitFrameMut
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Records.RecordGroups import RecordGroups
from convert.formats.Fusion.EntityCodec.Records.RecordScope import RecordScope
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.EmitGroupsMut import EmitGroupsMut
from convert.formats.Fusion.EntityCodec.Values.EmitValueMut import EmitValueMut
from convert.formats.Fusion.EntityCodec.Values.ValueQuota import ValueQuota
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


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
