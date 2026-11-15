from dataclasses import dataclass as MakeDataClass


# external target needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class ExternalTarget:
    SegmentId: int
    ObjectId: int
    ClassGuid: str
