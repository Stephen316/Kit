from dataclasses import dataclass as MakeDataClass


# axis specification needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class AxisSpec:
    CornerMm: tuple[float, float]
    FeatureName: str = "Axis"
