from dataclasses import dataclass


@dataclass(frozen=True)
class FaceGroup:
    GroupKey: int
    GroupId: str
