from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MetaIndex import SegmentKind


@MakeDataClass(frozen=True, slots=True)
class SegmentSlot:
    SegmentId: int
    Segment: SegmentKind
    UserName: str
