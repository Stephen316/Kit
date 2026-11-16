from math import isclose as IsClose

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.BossDepth import DepthDisplay, DepthReference

# metre precision permits floating point noise without conflating distinct saved planes
KPlaneTolerance = 1e-10


# a signed offset must come from the actual world datum normal and points
def PointOffset(
    Point: tuple[float, ...], Origin: tuple[float, ...], Normal: tuple[float, ...]
) -> float:
    return sum(
        (FirstValue - SecondValue) * AxisValue
        for FirstValue, SecondValue, AxisValue in zip(
            Point, Origin, Normal, strict=True
        )
    )


# the signed distance agrees with the driving magnitude and has no lateral drift
def SignedDistance(
    Display: DepthDisplay, Reference: DepthReference, Normal: tuple[float, ...]
) -> float:
    Points = Reference["points_metres"]
    Start, Endpoint = Points[:3], Points[3:6]
    Signed = PointOffset(Endpoint, Start, Normal)
    RequireArch(
        IsClose(
            abs(Signed),
            Display["dimension"]["metres"],
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        )
        and Display["dimension"]["metres"] > KPlaneTolerance,
        True,
        "signed scoped display agrees with its positive driving length",
    )
    RequireArch(
        all(
            IsClose(
                SecondValue - FirstValue,
                Signed * AxisValue,
                rel_tol=0,
                abs_tol=KPlaneTolerance,
            )
            for FirstValue, SecondValue, AxisValue in zip(
                Start, Endpoint, Normal, strict=True
            )
        ),
        True,
        "scoped display displacement is normal to the resolved support",
    )
    return Signed
