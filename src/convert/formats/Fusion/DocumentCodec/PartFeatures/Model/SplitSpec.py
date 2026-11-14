from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SplitSpec:
    PlaneIndex: int
    TargetBody: int = 1
    FeatureName: str = "Split Body"
