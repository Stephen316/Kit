from dataclasses import dataclass


@dataclass(frozen=True)
class CageLink:
    Previous: int
    NextLink: int
    Opposite: int
    VertexIndex: int
    FaceIndex: int
    EdgeIndex: int
    ValenceOffset: int = 0
