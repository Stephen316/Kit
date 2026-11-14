from dataclasses import dataclass


@dataclass(frozen=True)
class CageEdge:
    OriginLink: int
    KnotInterval: float = 1.0
