from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MoveSpec:
    OffsetMm: tuple[float, float, float]
    FeatureName: str = "Move"
    TurnDegrees: float = 0.0
