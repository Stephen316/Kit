from dataclasses import dataclass


# feature edge needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class FeatureEdge:
    First: int
    Second: int
