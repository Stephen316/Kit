from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ExternalTarget:
    SegmentId: int
    ObjectId: int
    ClassGuid: str
