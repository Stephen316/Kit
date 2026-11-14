from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FamilyRule:
    ClassName: str
    BaseName: str
    OperationCount: int
    TrackingType: int
