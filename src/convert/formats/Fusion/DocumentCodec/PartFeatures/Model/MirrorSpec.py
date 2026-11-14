from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MirrorSpec:
    SourceIndex: int
    PlaneIndex: int
    FeatureName: str = "Mirror"
