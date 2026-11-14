from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


@MakeDataClass(frozen=True, slots=True)
class ParsedSegment:
    Metadata: MetaSegment
    Records: tuple[EntityRecord, ...]
    Profile: EntityProfile
    BulkSlack: bytes = b""
