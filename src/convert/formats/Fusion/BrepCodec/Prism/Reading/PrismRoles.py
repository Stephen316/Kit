from dataclasses import dataclass as MakeDataClass


# prism roles needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismRoles:
    Corners: dict[int, int]
    Faces: dict[int, int]
    Edges: dict[int, int]
