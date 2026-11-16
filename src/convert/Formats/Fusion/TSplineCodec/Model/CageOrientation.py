from dataclasses import dataclass


# cage orientation needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CageOrientation:
    Spokes: tuple[int, ...]
    EdgeOrigins: tuple[tuple[int, int], ...]
