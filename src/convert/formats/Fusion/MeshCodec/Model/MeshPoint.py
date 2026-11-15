from dataclasses import dataclass


# mesh point needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class MeshPoint:
    XCoord: float
    YCoord: float
    ZCoord: float
