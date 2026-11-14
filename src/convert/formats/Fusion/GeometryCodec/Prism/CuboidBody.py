from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite


@MakeDataClass(frozen=True, slots=True)
class CuboidBody:
    Width: float
    Depth: float
    Height: float
    BasePoint: tuple[float, float, float]

    def __post_init__(self) -> None:
        if len(self.BasePoint) != 3:
            raise ValueError("Cuboid base must have three millimetre coordinates")
        Lengths = (self.Width, self.Depth, self.Height)
        if any(
            isinstance(Value, bool) or not IsFinite(Value)
            for Value in (*Lengths, *self.BasePoint)
        ):
            raise ValueError("Cuboid dimensions must be finite real numbers")
        if any(Value <= 0 or Value / 10 == 0 for Value in Lengths):
            raise ValueError("Cuboid dimensions must be positive representable lengths")
        for Origin, Length in zip(self.BasePoint, Lengths, strict=True):
            Upper = Origin + Length
            if not IsFinite(Upper) or Upper == Origin or Upper / 10 == Origin / 10:
                raise ValueError("Cuboid dimensions exceed coordinate precision")
