from dataclasses import dataclass as MakeDataClass

# the point pair shape must stay shared so native drawing authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the point triple shape must stay shared so native drawing authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]


# view draft needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class ViewDraft:
    Center: KPointPair
    ViewScale: float = 1.0
    EyeDirection: KPointTriple = (0.0, 0.0, -1.0)
    UpVector: KPointTriple = (0.0, 1.0, 0.0)
    Parent: int = -1
    ShowHidden: bool = False
