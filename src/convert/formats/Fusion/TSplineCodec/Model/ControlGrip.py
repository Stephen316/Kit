from dataclasses import dataclass


# control grip needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class ControlGrip:
    CoordX: float
    CoordY: float
    CoordZ: float
    Weight: float = 1.0
