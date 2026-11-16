from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.Formats.Fusion.EntityCodec.Records.CheckRoots import CheckRoots
from convert.Formats.Fusion.EntityCodec.Records.EmitEntity import EmitEntity
from convert.Formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxBulkBytes
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# the entities operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EncodeEntities(
    Records: tuple[EntityRecord, ...],
    Classes: tuple[MetaClass, ...],
    Profile: EntityProfile,
) -> tuple[BulkRecord, ...]:
    Catalog = BindProfile(Profile, Classes)
    IndexRows = tuple(
        BulkRecord(Record.TypeCode, Record.ObjectId, Record.IsPrimary, b"")
        for Record in Records
    )
    Scope = BindRecords(IndexRows, Classes)
    CheckRoots(Records)
    Emitted: list[BulkRecord] = []
    TotalBytes = 0
    for Record in Records:
        Encoded = EmitEntity(Record, Scope, Catalog)
        TotalBytes += len(Encoded.Payload)
        if TotalBytes > KMaxBulkBytes:
            raise ValueError("Fusion entity graph exceeds the byte limit")
        Emitted.append(Encoded)
    return tuple(Emitted)
