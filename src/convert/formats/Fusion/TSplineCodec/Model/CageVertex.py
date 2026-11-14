from dataclasses import dataclass


@dataclass(frozen=True)
class CageVertex:
    OriginLink: int
    Direction: str
