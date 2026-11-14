from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DrawingSlot:
    SegmentId: int
    UserName: str
    SegmentType: str
