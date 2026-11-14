from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.SubjectEntry import SubjectEntry


@MakeDataClass(frozen=True, slots=True)
class FeatureFrame:
    RootId: str
    Subjects: tuple[SubjectEntry, ...] | None
    HasNamedMeta: bool
