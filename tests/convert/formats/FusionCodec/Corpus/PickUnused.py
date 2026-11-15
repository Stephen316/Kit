from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMinClassCode
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from tests.convert.formats.FusionCodec.Entities.NativeGraph import NativeGraph


# shared pick unused setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
