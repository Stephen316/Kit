from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


@MakeDataClass(frozen=True, slots=True)
class NativeGraph:
    BulkData: bytes
    MetaData: bytes
    Metadata: MetaSegment
    Records: tuple[BulkRecord, ...]
    Targets: tuple[ExternalTarget, ...]
