from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface

# jump slack must remain consistent across callers so surface geometry retains the control cage shape
KJumpSlack = 1e-10


# span thirds needs an explicit validity boundary so surface geometry retains the control cage shape
def SpanThirds(Curve: BsCurve) -> list[list[float]]:
    Knots = [Curve.Knots[0]]
    for KnotValue, Count in zip(Curve.Knots, Curve.Multiplicity):
        Knots.extend([KnotValue] * Count)
    Knots.append(Curve.Knots[-1])
    Layers = [list(PoleValue) for PoleValue in Curve.Poles]
    for Order in (1, 2, 3):
        Scale = 4 - Order
        Spans = [
            Knots[Index + 4] - Knots[Index + Order] for Index in range(len(Layers) - 1)
        ]
        if any(Width <= 0.0 for Width in Spans):
            raise ValueError("Fusion grid conversion needs simple interior knots")
        Layers = [
            [
                Scale * (After - Before) / Spans[Index]
                for Before, After in zip(Layers[Index], Layers[Index + 1])
            ]
            for Index in range(len(Layers) - 1)
        ]
    return Layers


# third jumps needs an explicit validity boundary so surface geometry retains the control cage shape
def ThirdJumps(Curve: BsCurve) -> tuple[float, ...]:
    if Curve.Degree != 3 or Curve.Rational:
        raise ValueError("Fusion grid conversion needs nonrational cubic curves")
    Thirds = SpanThirds(Curve)
    return tuple(
        KnotValue
        for Index, KnotValue in enumerate(Curve.Knots[1:-1])
        if max(
            abs(Before - After)
            for Before, After in zip(Thirds[Index], Thirds[Index + 1])
        )
        > KJumpSlack
    )


# the union jumps contract needs a shared interpretation so surface geometry retains the control cage shape
def UnionJumps(Curves: list[BsCurve]) -> tuple[float, ...]:
    Found = {KnotValue for Curve in Curves for KnotValue in ThirdJumps(Curve)}
    return tuple(sorted(Found))


# the grid jumps contract needs a shared interpretation so surface geometry retains the control cage shape
def GridJumps(
    Surface: NubsSurface, Width: int, Height: int
) -> tuple[tuple[float, ...], ...]:
    KnotsU = tuple(KnotValue.Value for KnotValue in Surface.KnotsU)
    CountsU = tuple(KnotValue.Count for KnotValue in Surface.KnotsU)
    KnotsV = tuple(KnotValue.Value for KnotValue in Surface.KnotsV)
    CountsV = tuple(KnotValue.Count for KnotValue in Surface.KnotsV)
    Points = Surface.Points
    RowCurves = [
        BsCurve(
            False,
            3,
            0,
            KnotsU,
            CountsU,
            3,
            Points[RowIndex * Width : (RowIndex + 1) * Width],
            (),
        )
        for RowIndex in range(Height)
    ]
    ColumnCurves = [
        BsCurve(False, 3, 0, KnotsV, CountsV, 3, Points[ColumnIndex::Width], ())
        for ColumnIndex in range(Width)
    ]
    return ((), (), UnionJumps(RowCurves), (), (), UnionJumps(ColumnCurves))
