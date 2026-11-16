from dataclasses import dataclass as MakeDataClass


# entity reference needs an explicit state contract so display geometry retains its entity and scene relationships
@MakeDataClass(frozen=True, slots=True)
class EntityRef:
    SegmentId: int
    ObjectId: int
