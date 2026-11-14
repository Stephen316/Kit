from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Legacy.LegacyHeader import LegacyHeader
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


@MakeDataClass(frozen=True, slots=True)
class LegacySegment:
    Header: LegacyHeader
    Classes: tuple[MetaClass, ...]
    StoredIds: tuple[int, ...]
    NextId: int
    Records: tuple[BulkRecord, ...]
