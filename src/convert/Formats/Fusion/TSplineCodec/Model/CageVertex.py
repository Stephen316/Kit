from dataclasses import dataclass


# cage vertex needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CageVertex:
    OriginLink: int
    Direction: str
