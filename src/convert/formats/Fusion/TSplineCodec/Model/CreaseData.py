from dataclasses import dataclass


@dataclass(frozen=True)
class CreaseData:
    EdgeIndices: tuple[int, ...]
    VertexIndices: tuple[int, ...]
