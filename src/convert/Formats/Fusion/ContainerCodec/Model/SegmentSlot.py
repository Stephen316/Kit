from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.MetaIndex import SegmentKind


# segment slot needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class SegmentSlot:
    SegmentId: int
    Segment: SegmentKind
    UserName: str
