from dataclasses import dataclass


# cage link needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class CageLink:
    Previous: int
    NextLink: int
    Opposite: int
    VertexIndex: int
    FaceIndex: int
    EdgeIndex: int
    ValenceOffset: int = 0
