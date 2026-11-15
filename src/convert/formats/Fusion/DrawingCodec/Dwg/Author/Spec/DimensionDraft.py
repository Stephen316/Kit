from dataclasses import dataclass as MakeDataClass

# the point pair shape must stay shared so native drawing authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the dimension kinds order must stay explicit so drawing objects retain valid ownership and reference relationships
KDimensionKinds = ("Horizontal", "Vertical", "Aligned", "Radius", "Diameter")


# dimension draft needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DimensionDraft:
    FirstPoint: KPointPair
    SecondPoint: KPointPair
    LineHeight: float
    ViewScale: float = 1.0
    DimensionKind: str = "Horizontal"
