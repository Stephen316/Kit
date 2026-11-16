from dataclasses import dataclass as MakeDataClass


# drawing slot needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingSlot:
    SegmentId: int
    UserName: str
    SegmentType: str
