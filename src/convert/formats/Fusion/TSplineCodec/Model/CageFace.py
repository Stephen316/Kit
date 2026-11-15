from dataclasses import dataclass


# cage face needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CageFace:
    OriginLink: int
    IsHidden: bool = False
