from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.SubjectEntry import SubjectEntry


# feature frame needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class FeatureFrame:
    RootId: str
    Subjects: tuple[SubjectEntry, ...] | None
    HasNamedMeta: bool
