from dataclasses import dataclass


@dataclass(frozen=True)
class ControlGrip:
    CoordX: float
    CoordY: float
    CoordZ: float
    Weight: float = 1.0
