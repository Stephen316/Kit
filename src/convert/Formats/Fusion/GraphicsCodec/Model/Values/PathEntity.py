from dataclasses import dataclass as MakeDataClass


# path entity needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class PathEntity:
    SegmentId: int
    ObjectId: int
