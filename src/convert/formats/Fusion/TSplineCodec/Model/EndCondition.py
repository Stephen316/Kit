from dataclasses import dataclass


@dataclass(frozen=True)
class EndCondition:
    EdgeIndex: int
    EndValue: float
