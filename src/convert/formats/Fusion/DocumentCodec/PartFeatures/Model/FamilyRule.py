from dataclasses import dataclass as MakeDataClass


# family rule needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class FamilyRule:
    ClassName: str
    BaseName: str
    OperationCount: int
    TrackingType: int
