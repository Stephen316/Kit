from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.CheckRoots import CheckRoots
from convert.formats.Fusion.EntityCodec.Records.ReadEntity import ReadEntity
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def DecodeEntities(
    Records: tuple[BulkRecord, ...],
    Classes: tuple[MetaClass, ...],
    Profile: EntityProfile,
) -> tuple[EntityRecord, ...]:
    Catalog = BindProfile(Profile, Classes)
    Scope = BindRecords(Records, Classes)
    Values = tuple(ReadEntity(Record, Scope, Catalog) for Record in Records)
    CheckRoots(Values)
    return Values
