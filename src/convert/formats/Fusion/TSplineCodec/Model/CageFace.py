from dataclasses import dataclass


@dataclass(frozen=True)
class CageFace:
    OriginLink: int
    IsHidden: bool = False
