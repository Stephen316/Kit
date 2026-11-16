from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile


# auxiliary graph needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class AuxiliaryGraph:
    Streams: SegmentStreams
    Records: tuple[EntityRecord, ...]
    Profile: EntityProfile
