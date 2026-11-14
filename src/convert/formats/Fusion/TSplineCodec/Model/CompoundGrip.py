from dataclasses import dataclass


@dataclass(frozen=True)
class CompoundGrip:
    VertexIndex: int
    SpokeLengths: tuple[int, ...]
    GripIndices: tuple[int, ...]
