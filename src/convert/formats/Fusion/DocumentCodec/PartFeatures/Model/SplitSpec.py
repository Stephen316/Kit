from dataclasses import dataclass as MakeDataClass


# split specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class SplitSpec:
    PlaneIndex: int
    TargetBody: int = 1
    FeatureName: str = "Split Body"
