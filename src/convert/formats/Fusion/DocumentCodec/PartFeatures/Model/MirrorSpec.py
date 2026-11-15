from dataclasses import dataclass as MakeDataClass


# mirror specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class MirrorSpec:
    SourceIndex: int
    PlaneIndex: int
    FeatureName: str = "Mirror"
