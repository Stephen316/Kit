from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureEdge:
    First: int
    Second: int
