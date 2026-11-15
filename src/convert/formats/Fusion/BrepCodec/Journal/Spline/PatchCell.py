from dataclasses import dataclass as MakeDataClass


# patch cell needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class PatchCell:
    Face: int
    Window: tuple[float, float, float, float]
    Offset: tuple[float, float, int]
