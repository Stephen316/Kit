from dataclasses import dataclass


@dataclass(frozen=True)
class MeshPoint:
    XCoord: float
    YCoord: float
    ZCoord: float
