from dataclasses import dataclass


# compound grip needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CompoundGrip:
    VertexIndex: int
    SpokeLengths: tuple[int, ...]
    GripIndices: tuple[int, ...]
