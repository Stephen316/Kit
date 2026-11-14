from dataclasses import dataclass as MakeDataClass

KPointPair = tuple[float, float]
KDimensionKinds = ("Horizontal", "Vertical", "Aligned", "Radius", "Diameter")


@MakeDataClass(frozen=True, slots=True)
class DimensionDraft:
    FirstPoint: KPointPair
    SecondPoint: KPointPair
    LineHeight: float
    ViewScale: float = 1.0
    DimensionKind: str = "Horizontal"
