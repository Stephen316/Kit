from dataclasses import dataclass


# face group needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class FaceGroup:
    GroupKey: int
    GroupId: str
