from dataclasses import dataclass


@dataclass(frozen=True)
class IndexPair:
    SourceIndex: int
    TargetIndex: int
