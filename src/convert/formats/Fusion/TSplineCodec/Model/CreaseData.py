from dataclasses import dataclass


# crease data needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CreaseData:
    EdgeIndices: tuple[int, ...]
    VertexIndices: tuple[int, ...]
