from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.Formats.Fusion.EntityCodec.Records.CheckRoots import CheckRoots
from convert.Formats.Fusion.EntityCodec.Records.ReadEntity import ReadEntity
from convert.Formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# the entities operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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
