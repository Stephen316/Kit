from dataclasses import dataclass as MakeDataClass


# the specification operation needs an explicit state contract so feature parameters remain connected to the resulting geometry
@MakeDataClass(frozen=True, slots=True)
class PointSpec:
    CornerMm: tuple[float, float]
    FeatureName: str = "Point"
