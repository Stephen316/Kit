from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite


@MakeDataClass(frozen=True, slots=True)
class CylinderBody:
    Radius: float
    Height: float
    BasePoint: tuple[float, float, float]

    def __post_init__(self) -> None:
        if len(self.BasePoint) != 3:
            raise ValueError("Cylinder base must have three millimetre coordinates")
        Values = (self.Radius, self.Height, *self.BasePoint)
        if any(isinstance(Value, bool) or not IsFinite(Value) for Value in Values):
            raise ValueError("Cylinder dimensions must be finite real numbers")
        if self.Radius <= 0 or self.Height <= 0:
            raise ValueError("Cylinder radius and height must be positive")
        Limits = tuple(
            Coord + SignValue * self.Radius
            for Coord in self.BasePoint[:2]
            for SignValue in (-1, 1)
        ) + (self.BasePoint[2] + self.Height,)
        if not all(IsFinite(Value) for Value in Limits):
            raise ValueError("Cylinder dimensions exceed finite coordinate range")
        Bases = (
            (self.BasePoint[0],) * 2 + (self.BasePoint[1],) * 2 + (self.BasePoint[2],)
        )
        if any(Value == Origin for Value, Origin in zip(Limits, Bases)):
            raise ValueError("Cylinder dimensions collapse at coordinate precision")
