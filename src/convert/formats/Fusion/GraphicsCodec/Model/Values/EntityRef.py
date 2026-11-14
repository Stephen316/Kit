from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EntityRef:
    SegmentId: int
    ObjectId: int
