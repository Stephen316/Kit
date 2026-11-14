from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PatchCell:
    Face: int
    Window: tuple[float, float, float, float]
    Offset: tuple[float, float, int]
