from math import isfinite as IsFinite, ulp as FloatUlp


# cancellation between radial projections may leave signed noise on the axis
def RadialLevel(BaseValue: float, AlongX: float, AlongY: float) -> float:
    Radius = BaseValue + AlongX + AlongY
    Scale = max(abs(BaseValue), abs(AlongX), abs(AlongY))
    if IsFinite(Scale) and abs(Radius) <= 8.0 * FloatUlp(Scale):
        return 0.0
    return Radius


# joining adjacent roundoff levels keeps vertices and analytic carriers on the same coordinates
def JoinLevels(Values: tuple[float, ...], Tolerance: float) -> tuple[float, ...]:
    Labels = list(range(len(Values)))
    for Index, First in enumerate(Values):
        Following = (Index + 1) % len(Values)
        if abs(First - Values[Following]) <= Tolerance:
            Start, EndValue = Labels[Index], Labels[Following]
            Labels = [Start if Label == EndValue else Label for Label in Labels]
    return tuple(Values[Label] for Label in Labels)


# projected rectangles need common exact radii and heights for their trimmed carriers
def CleanMeridian(
    Meridian: tuple[tuple[float, float], ...], Tolerance: float
) -> tuple[tuple[float, float], ...]:
    Radii = JoinLevels(tuple(Radius for Radius, _ in Meridian), Tolerance)
    Heights = JoinLevels(tuple(Height for _, Height in Meridian), Tolerance)
    return tuple(zip(Radii, Heights, strict=True))
