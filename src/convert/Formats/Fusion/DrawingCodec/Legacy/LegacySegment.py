from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Legacy.LegacyHeader import LegacyHeader
from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


# legacy segment needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class LegacySegment:
    Header: LegacyHeader
    Classes: tuple[MetaClass, ...]
    StoredIds: tuple[int, ...]
    NextId: int
    Records: tuple[BulkRecord, ...]
