from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# subject value needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class SubjectValue:
    Target: LocalRef | SegmentRef | CrossRef | None
    ObserverIndex: int
