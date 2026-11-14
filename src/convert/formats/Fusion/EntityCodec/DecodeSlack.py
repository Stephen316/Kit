from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.CheckRoots import CheckRoots
from convert.formats.Fusion.EntityCodec.Records.ReadEntity import ReadEntity, ReadSlack
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def DecodeSlack(
    Records: tuple[BulkRecord, ...],
    Classes: tuple[MetaClass, ...],
    Profile: EntityProfile,
) -> tuple[tuple[EntityRecord, ...], bytes]:
    if not Records:
        raise ValueError("Fusion bulk slack needs a final record")
    Catalog = BindProfile(Profile, Classes)
    Scope = BindRecords(Records, Classes)
    Leading = tuple(ReadEntity(Record, Scope, Catalog) for Record in Records[:-1])
    Final, Slack = ReadSlack(Records[-1], Scope, Catalog)
    Values = Leading + (Final,)
    CheckRoots(Values)
    return Values, Slack
