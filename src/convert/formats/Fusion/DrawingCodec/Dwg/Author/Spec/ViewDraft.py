from dataclasses import dataclass as MakeDataClass

KPointPair = tuple[float, float]
KPointTriple = tuple[float, float, float]


@MakeDataClass(frozen=True, slots=True)
class ViewDraft:
    Center: KPointPair
    ViewScale: float = 1.0
    EyeDirection: KPointTriple = (0.0, 0.0, -1.0)
    UpVector: KPointTriple = (0.0, 1.0, 0.0)
    Parent: int = -1
    ShowHidden: bool = False
