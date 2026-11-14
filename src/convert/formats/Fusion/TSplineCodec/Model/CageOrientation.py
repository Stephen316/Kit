from dataclasses import dataclass


@dataclass(frozen=True)
class CageOrientation:
    Spokes: tuple[int, ...]
    EdgeOrigins: tuple[tuple[int, int], ...]
