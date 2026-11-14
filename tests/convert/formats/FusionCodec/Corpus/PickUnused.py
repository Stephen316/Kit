from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMinClassCode
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from tests.convert.formats.FusionCodec.Entities.NativeGraph import NativeGraph


def PickUnused(Source: NativeGraph) -> MetaClass:
    Bases = {Entry.BaseGuid.upper() for Entry in Source.Metadata.Classes}
    Codes = {Record.TypeCode for Record in Source.Records}
    return next(
        Entry
        for CodeValue, Entry in enumerate(Source.Metadata.Classes, KMinClassCode)
        if not Entry.OwnerIds
        and Entry.ClassGuid.upper() not in Bases
        and CodeValue not in Codes
    )
