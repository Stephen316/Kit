from dataclasses import dataclass


# cage edge needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CageEdge:
    OriginLink: int
    KnotInterval: float = 1.0
