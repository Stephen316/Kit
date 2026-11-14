from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class OffsetSpec:
    DistanceMm: float
    FeatureName: str = "Offset"
    SideMm: tuple[float, float] | None = None
