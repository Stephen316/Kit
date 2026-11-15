from dataclasses import dataclass as MakeDataClass


# move specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class MoveSpec:
    OffsetMm: tuple[float, float, float]
    FeatureName: str = "Move"
    TurnDegrees: float = 0.0
