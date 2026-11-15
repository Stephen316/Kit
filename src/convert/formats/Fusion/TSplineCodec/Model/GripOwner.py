from dataclasses import dataclass


# grip owner needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class GripOwner:
    VertexIndex: int
    IsPrimary: bool
