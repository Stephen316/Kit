from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FatPoint:
    Width: int
    Height: int
    BoxSize: tuple[float, ...]
