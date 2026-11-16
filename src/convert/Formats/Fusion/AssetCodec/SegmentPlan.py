from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# segment authoring keeps typed payloads separate from derived index positions
@MakeDataClass(frozen=True, slots=True)
class SegmentPlan:
    Metadata: MetaSegment
    Records: tuple[BulkRecord, ...]
