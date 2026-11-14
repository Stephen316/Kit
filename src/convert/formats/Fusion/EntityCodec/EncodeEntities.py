from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.CheckRoots import CheckRoots
from convert.formats.Fusion.EntityCodec.Records.EmitEntity import EmitEntity
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxBulkBytes
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


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
