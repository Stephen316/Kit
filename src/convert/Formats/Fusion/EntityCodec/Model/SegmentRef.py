from dataclasses import dataclass as MakeDataClass


# segment reference needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class SegmentRef:
    ObjectId: int
    SegmentId: int
