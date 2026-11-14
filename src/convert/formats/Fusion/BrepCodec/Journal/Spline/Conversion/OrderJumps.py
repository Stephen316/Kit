from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot

KOrderSlack = 1e-10
KOrderDegree = 3
KPeriodicClosure = 2


def SpreadKnots(Values: tuple[float, ...], Counts: tuple[int, ...]) -> list[float]:
    Spread = [Values[0]]
    for KnotValue, Count in zip(Values, Counts):
        Spread.extend([KnotValue] * Count)
    Spread.append(Values[-1])
    return Spread


def DeriveLevel(
    Knots: list[float], Poles: list[list[float]], Level: int
) -> list[list[float]]:
    Scale = KOrderDegree - Level + 1
    Derived: list[list[float]] = []
    for Index in range(len(Poles) - 1):
        Width = Knots[Index + KOrderDegree + 1] - Knots[Index + Level]
        Derived.append(
            [
                Scale * (After - Before) / Width if Width > 0.0 else 0.0
                for Before, After in zip(Poles[Index], Poles[Index + 1])
            ]
        )
    return Derived


def SpanValue(
    Knots: list[float],
    Poles: list[list[float]],
    Level: int,
    SpanIndex: int,
    Param: float,
) -> list[float]:
    Degree = KOrderDegree - Level
    Shifted = Knots[Level : len(Knots) - Level]
    Local = SpanIndex - Level
    Points = [list(Poles[Local - Degree + Offset]) for Offset in range(Degree + 1)]
    for Round in range(1, Degree + 1):
        for Offset in range(Degree, Round - 1, -1):
            Start = Shifted[Local - Degree + Offset]
            Width = Shifted[Local + 1 + Offset - Round] - Start
            Alpha = (Param - Start) / Width
            Points[Offset] = [
                (1.0 - Alpha) * Before + Alpha * After
                for Before, After in zip(Points[Offset - 1], Points[Offset])
            ]
    return Points[Degree]


def PoleLevels(
    Knots: list[float], Poles: tuple[tuple[float, ...], ...]
) -> list[list[list[float]]]:
    Levels = [[list(PoleValue) for PoleValue in Poles]]
    for Level in (1, 2, 3):
        Levels.append(DeriveLevel(Knots, Levels[-1], Level))
    return Levels


def SeamOrders(
    Knots: list[float], Poles: tuple[tuple[float, ...], ...]
) -> dict[float, int]:
    Levels = PoleLevels(Knots, Poles)
    First = max(Index for Index, Value in enumerate(Knots) if Value == Knots[0])
    Final = max(Index for Index, Value in enumerate(Knots) if Value < Knots[-1])
    for Level in (1, 2, 3):
        Before = SpanValue(Knots, Levels[Level], Level, Final, Knots[-1])
        After = SpanValue(Knots, Levels[Level], Level, First, Knots[0])
        if (
            max(
                abs(BeforeValue - AfterValue)
                for BeforeValue, AfterValue in zip(Before, After)
            )
            > KOrderSlack
        ):
            return {Knots[0]: Level}
    return {}


def KnotOrders(
    Knots: list[float], Poles: tuple[tuple[float, ...], ...], Periodic: bool = False
) -> dict[float, int]:
    Levels = PoleLevels(Knots, Poles)
    Orders: dict[float, int] = SeamOrders(Knots, Poles) if Periodic else {}
    Inner = Knots[KOrderDegree + 1 : len(Knots) - KOrderDegree - 1]
    for KnotValue in sorted(set(Inner)):
        LeftSpan = max(Index for Index, Value in enumerate(Knots) if Value < KnotValue)
        RightSpan = (
            min(Index for Index, Value in enumerate(Knots) if Value > KnotValue) - 1
        )
        for Level in (1, 2, 3):
            Before = SpanValue(Knots, Levels[Level], Level, LeftSpan, KnotValue)
            After = SpanValue(Knots, Levels[Level], Level, RightSpan, KnotValue)
            if (
                max(
                    abs(BeforeValue - AfterValue)
                    for BeforeValue, AfterValue in zip(Before, After)
                )
                > KOrderSlack
            ):
                Orders[KnotValue] = Level
                break
    return Orders


def SplitOrders(
    Merged: dict[float, int],
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    return (
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 1)),
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 2)),
        tuple(sorted(Value for Value, Level in Merged.items() if Level == 3)),
    )


def MassPoles(
    Poles: tuple[tuple[float, ...], ...], Weights: tuple[float, ...]
) -> tuple[tuple[float, ...], ...]:
    if len(Poles) != len(Weights):
        raise ValueError("Fusion jump orders need one weight per pole")
    return tuple(
        (*(Entry * WeightValue for Entry in PoleValue), WeightValue)
        for PoleValue, WeightValue in zip(Poles, Weights)
    )


def CurveOrders(
    Curve: BsCurve,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    if Curve.Degree != KOrderDegree:
        raise ValueError("Fusion jump orders need cubic curves")
    Knots = SpreadKnots(Curve.Knots, Curve.Multiplicity)
    Periodic = Curve.Closure == KPeriodicClosure
    if Curve.Rational:
        Masses = MassPoles(Curve.Poles, Curve.Weights)
        return SplitOrders(KnotOrders(Knots, Masses, Periodic))
    return SplitOrders(KnotOrders(Knots, Curve.Poles, Periodic))


def MergeOrders(
    Knots: tuple[SplineKnot, ...],
    Lines: list[tuple[tuple[float, ...], ...]],
    Periodic: bool = False,
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]:
    Spread = SpreadKnots(
        tuple(KnotValue.Value for KnotValue in Knots),
        tuple(KnotValue.Count for KnotValue in Knots),
    )
    Merged: dict[float, int] = {}
    for LineValue in Lines:
        for KnotValue, Level in KnotOrders(Spread, LineValue, Periodic).items():
            Merged[KnotValue] = min(Level, Merged.get(KnotValue, Level))
    return SplitOrders(Merged)


def SurfaceOrders(Surface: NubsSurface) -> tuple[tuple[float, ...], ...]:
    if (Surface.DegreeU, Surface.DegreeV) != (KOrderDegree, KOrderDegree):
        raise ValueError("Fusion jump orders need bicubic surfaces")
    Width = sum(KnotValue.Count for KnotValue in Surface.KnotsU) - 2
    Height = len(Surface.Points) // Width
    Points = (
        MassPoles(Surface.Points, Surface.Weights)
        if Surface.Weights
        else Surface.Points
    )
    if Width * Height != len(Points):
        raise ValueError("Fusion jump orders found a ragged pole grid")
    RowLines = [Points[Index * Width : (Index + 1) * Width] for Index in range(Height)]
    Columns = [Points[Index::Width] for Index in range(Width)]
    return (
        *MergeOrders(Surface.KnotsU, RowLines, Surface.ClosureU == KPeriodicClosure),
        *MergeOrders(Surface.KnotsV, Columns, Surface.ClosureV == KPeriodicClosure),
    )
