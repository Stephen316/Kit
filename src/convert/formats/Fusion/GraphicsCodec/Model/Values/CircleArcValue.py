from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CircleArcValue:
    Sampling: int
    Interval: tuple[float, ...]
    Radius: float
    Center: tuple[float, ...]
    Normal: tuple[float, ...]
    StartAngle: float
    EndAngle: float
    ReferencePoint: tuple[float, ...]
