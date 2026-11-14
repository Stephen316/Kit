from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PrismRoles:
    Corners: dict[int, int]
    Faces: dict[int, int]
    Edges: dict[int, int]
