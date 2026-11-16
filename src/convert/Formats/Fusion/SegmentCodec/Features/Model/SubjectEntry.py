from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# subject entry needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class SubjectEntry:
    SubjectRef: LocalRef
    ObserverIndex: int
