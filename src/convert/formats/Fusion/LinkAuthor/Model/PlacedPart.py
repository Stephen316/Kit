from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class PlacedPart:
    TargetIndex: int
    Matrix: tuple[float, ...]
    Grounded: bool = False
