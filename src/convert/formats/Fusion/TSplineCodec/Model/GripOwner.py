from dataclasses import dataclass


@dataclass(frozen=True)
class GripOwner:
    VertexIndex: int
    IsPrimary: bool
