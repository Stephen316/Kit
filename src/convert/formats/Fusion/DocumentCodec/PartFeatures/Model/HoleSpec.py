from dataclasses import dataclass as MakeDataClass


# hole specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class HoleSpec:
    CenterMm: tuple[float, float]
    DiameterMm: float
    DepthMm: float = 0.0
    BoreDiameterMm: float = 0.0
    BoreDepthMm: float = 0.0
    FeatureName: str = "Hole"
    SinkDiameterMm: float = 0.0
    SinkAngleDegrees: float = 90.0
