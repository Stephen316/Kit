from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KPolePlace,
    FacePlan,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import KEndCount
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KIndexedRow,
    BlendRows,
)

KKnotList = tuple[Fraction, ...]
KLineRows = tuple[KKnotList, list[KIndexedRow]]
KCurveRows = tuple[tuple[float, ...], tuple[int, ...], list[KIndexedRow]]


def Negated(Knots: KKnotList) -> KKnotList:
    return tuple(-Value for Value in reversed(Knots))


def SidePoles(
    PlanValue: FacePlan, GridRows: dict[KPolePlace, KIndexedRow], SideIndex: int
) -> KLineRows:
    CountU, CountV = len(PlanValue.FullU) - 4, len(PlanValue.FullV) - 4
    if SideIndex == 0:
        return (PlanValue.FullU, [GridRows[(0, Column)] for Column in range(CountU)])
    if SideIndex == 1:
        return (
            PlanValue.FullV,
            [GridRows[(RowIndex, CountU - 1)] for RowIndex in range(CountV)],
        )
    if SideIndex == 2:
        Places = [(CountV - 1, Column) for Column in reversed(range(CountU))]
        return (Negated(PlanValue.FullU), [GridRows[Place] for Place in Places])
    Places = [(RowIndex, 0) for RowIndex in reversed(range(CountV))]
    return (Negated(PlanValue.FullV), [GridRows[Place] for Place in Places])


def InsertKnot(
    Knots: KKnotList, Poles: list[KIndexedRow], Value: Fraction
) -> KLineRows:
    SpanIndex = max(
        Index
        for Index in range(len(Knots) - 1)
        if Knots[Index] <= Value < Knots[Index + 1]
    )
    Fresh: list[KIndexedRow] = []
    for Index in range(len(Poles) + 1):
        if Index <= SpanIndex - 3:
            Fresh.append(Poles[Index])
        elif Index >= SpanIndex + 1:
            Fresh.append(Poles[Index - 1])
        else:
            Alpha = (Value - Knots[Index]) / (Knots[Index + 3] - Knots[Index])
            Fresh.append(BlendRows(Poles[Index - 1], Poles[Index], float(Alpha)))
    return (Knots[: SpanIndex + 1] + (Value,) + Knots[SpanIndex + 1 :], Fresh)


def ClampKnot(LineRows: KLineRows, Value: Fraction) -> KLineRows:
    Knots, Poles = LineRows
    if Knots.count(Value) > KEndCount or not Knots[0] < Value < Knots[-1]:
        return LineRows
    while Knots.count(Value) < KEndCount:
        Knots, Poles = InsertKnot(Knots, Poles, Value)
    return (Knots, Poles)


def CurveRows(
    PlanValue: FacePlan,
    GridRows: dict[KPolePlace, KIndexedRow],
    CurveValue: CappedCurve,
) -> KCurveRows:
    Lower, Upper = Fraction(CurveValue.Lower), Fraction(CurveValue.Upper)
    LineRows = SidePoles(PlanValue, GridRows, CurveValue.Side)
    Knots, Poles = ClampKnot(ClampKnot(LineRows, Lower), Upper)
    StartPole = Knots.index(Lower) + Knots.count(Lower) - 4
    FinalPole = Knots.index(Upper) - 1
    Inner = sorted({Value for Value in Knots if Lower < Value < Upper})
    return (
        (float(Lower),) + tuple(float(Value) for Value in Inner) + (float(Upper),),
        (KEndCount,) + tuple(Knots.count(Value) for Value in Inner) + (KEndCount,),
        Poles[StartPole : FinalPole + 1],
    )


def SpanOf(Knots: KKnotList, Value: Fraction) -> int:
    Spans = [
        Index for Index in range(len(Knots) - 1) if Knots[Index] < Knots[Index + 1]
    ]
    Inside = [Index for Index in Spans if Knots[Index] <= Value < Knots[Index + 1]]
    return Inside[-1] if Inside else Spans[-1]


def DeBoorRow(
    Knots: KKnotList, SpanIndex: int, Value: Fraction, Points: list[KIndexedRow]
) -> KIndexedRow:
    Working = list(Points)
    for Level in range(1, 4):
        for Place in range(3, Level - 1, -1):
            Index = SpanIndex - 3 + Place
            Alpha = (Value - Knots[Index]) / (Knots[Index + 4 - Level] - Knots[Index])
            Working[Place] = BlendRows(Working[Place - 1], Working[Place], float(Alpha))
    return Working[3]


def SurfacePoint(
    PlanValue: FacePlan,
    GridRows: dict[KPolePlace, KIndexedRow],
    PointU: Fraction,
    PointV: Fraction,
) -> KIndexedRow:
    SpanU = SpanOf(PlanValue.FullU, PointU)
    SpanV = SpanOf(PlanValue.FullV, PointV)
    Lines = [
        DeBoorRow(
            PlanValue.FullU,
            SpanU,
            PointU,
            [GridRows[(RowIndex, Column)] for Column in range(SpanU - 3, SpanU + 1)],
        )
        for RowIndex in range(SpanV - 3, SpanV + 1)
    ]
    return DeBoorRow(PlanValue.FullV, SpanV, PointV, Lines)
