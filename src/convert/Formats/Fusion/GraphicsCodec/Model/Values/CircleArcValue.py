from dataclasses import dataclass as MakeDataClass


# circle arc value needs an explicit state contract so display geometry retains its entity and scene relationships
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
