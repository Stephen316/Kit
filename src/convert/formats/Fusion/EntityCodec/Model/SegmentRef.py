from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SegmentRef:
    ObjectId: int
    SegmentId: int
