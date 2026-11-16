from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


# parsed segment needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class ParsedSegment:
    Metadata: MetaSegment
    Records: tuple[EntityRecord, ...]
    Profile: EntityProfile
    BulkSlack: bytes = b""
