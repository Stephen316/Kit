from math import isfinite as IsFinite


def CheckRimFit(
    BottomRadius: float,
    TopRadius: float,
    Height: float,
    BasePoint: tuple[float, float, float],
) -> None:
    for Radius in (BottomRadius, TopRadius):
        for Origin in BasePoint[:2]:
            for Offset in (-Radius, Radius):
                Extent = Origin + Offset
                if (
                    not IsFinite(Extent)
                    or Extent == Origin
                    or Extent / 10 == Origin / 10
                ):
                    raise ValueError("Frustum rim exceeds coordinate precision")
    TopHeight = BasePoint[2] + Height
    if (
        not IsFinite(TopHeight)
        or TopHeight == BasePoint[2]
        or TopHeight / 10 == BasePoint[2] / 10
    ):
        raise ValueError("Frustum height exceeds coordinate precision")
