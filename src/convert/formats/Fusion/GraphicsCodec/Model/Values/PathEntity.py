from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PathEntity:
    SegmentId: int
    ObjectId: int
