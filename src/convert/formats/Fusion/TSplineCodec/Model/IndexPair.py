from dataclasses import dataclass


# index pair needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class IndexPair:
    SourceIndex: int
    TargetIndex: int
