from dataclasses import dataclass


# end condition needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class EndCondition:
    EdgeIndex: int
    EndValue: float
