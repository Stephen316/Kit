from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ConeFrame:
    OriginCm: tuple[float, float, float]
    Axis: tuple[float, float, float]
    MajorVectorCm: tuple[float, float, float]
    Ratio: float
    SineAngle: float
    CosineAngle: float
    ScaleCm: float
    ReverseSense: bool
