from dataclasses import dataclass


# octa normal needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class OctaNormal:
    First: float
    Second: float
