from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import (
    CappedLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.SolveCaps import SolveCaps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import (
    CurveOrders,
    SurfaceOrders,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapHook
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleTable import BuildTable
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.FaceResult import (
    FaceResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilRows import (
    Cartesian,
    EvaluateRows,
    PickPoint,
    StencilRows,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface

KRationalForm = "both"
KPeriodicClosure = 2
KClosedClosure = 1
KRowSlack = 1e-12


def IsRational(Values: StencilRows, Indices: tuple[int, ...]) -> bool:
    return any(Values.Weighted[Index] for Index in Indices)


def MakeFace(
    FaceValue: StencilFace, Values: StencilRows, Closure: tuple[int, int] = (0, 0)
) -> FaceResult:
    Indices = FaceValue.Poles
    if IsRational(Values, Indices):
        Masses = tuple(Values.Homogeneous[Index] for Index in Indices)
        Points = tuple(Cartesian(MassValue) for MassValue in Masses)
        Weights = tuple(MassValue[3] for MassValue in Masses)
        Result = NubsSurface(
            3,
            3,
            Closure[0],
            Closure[1],
            0,
            0,
            FaceValue.KnotsU,
            FaceValue.KnotsV,
            Points,
            Weights,
            KRationalForm,
        )
    else:
        Points = tuple(Values.Points[Index] for Index in Indices)
        Result = NubsSurface(
            3,
            3,
            Closure[0],
            Closure[1],
            0,
            0,
            FaceValue.KnotsU,
            FaceValue.KnotsV,
            Points,
        )
    return FaceResult(FaceValue.FaceIndex, Result, SurfaceOrders(Result))


def MakeCurve(
    CurveValue: StencilCurve, Values: StencilRows, Closure: int = 0
) -> BsCurve:
    Indices = CurveValue.Poles
    Knots, Counts = CurveValue.Knots, CurveValue.Multiplicity
    if IsRational(Values, Indices):
        Masses = tuple(Values.Homogeneous[Index] for Index in Indices)
        Poles = tuple(Cartesian(MassValue) for MassValue in Masses)
        Weights = tuple(MassValue[3] for MassValue in Masses)
        return BsCurve(True, 3, Closure, Knots, Counts, 3, Poles, Weights)
    Poles = tuple(Values.Points[Index] for Index in Indices)
    return BsCurve(False, 3, Closure, Knots, Counts, 3, Poles, ())


def IsSameRows(Table: StencilTable, First: int, Second: int) -> bool:
    Former, Latter = dict(Table.Rows[First]), dict(Table.Rows[Second])
    return all(
        abs(Former.get(GripIndex, 0.0) - Latter.get(GripIndex, 0.0)) <= KRowSlack
        for GripIndex in Former.keys() | Latter.keys()
    )


def SeamClosure(
    Table: StencilTable, Starts: tuple[int, ...], Finals: tuple[int, ...], Period: int
) -> int:
    if Period:
        return KPeriodicClosure
    IsClosed = all(
        IsSameRows(Table, First, Final) for First, Final in zip(Starts, Finals)
    )
    return KClosedClosure if IsClosed else 0


def FaceClosure(
    Table: StencilTable, Shape: CappedShape, FaceValue: StencilFace
) -> tuple[int, int]:
    PeriodU, PeriodV = Shape.Periods[FaceValue.FaceIndex]
    Width = sum(KnotValue.Count for KnotValue in FaceValue.KnotsU) - 2
    Poles = FaceValue.Poles
    Lines = [Poles[Start : Start + Width] for Start in range(0, len(Poles), Width)]
    return (
        SeamClosure(
            Table,
            tuple(LineValue[0] for LineValue in Lines),
            tuple(LineValue[-1] for LineValue in Lines),
            PeriodU,
        ),
        SeamClosure(Table, Lines[0], Lines[-1], PeriodV),
    )


def CurveClosure(Table: StencilTable, CurveValue: StencilCurve, Closure: int) -> int:
    EndRows = (CurveValue.Poles[:1], CurveValue.Poles[-1:])
    return SeamClosure(Table, *EndRows, Closure == KPeriodicClosure)


def ApplyStencil(
    Table: StencilTable, Surface: TsplineSurface, Shape: CappedShape
) -> CageResult:
    if len(Surface.Grips) != Table.GripCount:
        raise ValueError("Fusion Form stencil needs the table grip count")
    if len(Table.Curves) != len(Shape.Curves):
        raise ValueError("Fusion Form conversion found curves without poles")
    Values = EvaluateRows(Table.Rows, Surface.Grips)
    Faces = tuple(
        MakeFace(FaceValue, Values, FaceClosure(Table, Shape, FaceValue))
        for FaceValue in Table.Faces
    )
    Curves = tuple(
        MakeCurve(
            CurveValue, Values, CurveClosure(Table, CurveValue, PlanValue.Closure)
        )
        for CurveValue, PlanValue in zip(Table.Curves, Shape.Curves)
    )
    return CageResult(
        Faces,
        Curves,
        tuple(CurveOrders(Curve) for Curve in Curves),
        tuple(PickPoint(Values, Index) for Index in Table.Points),
    )


def CageParts(
    Surface: TsplineSurface, CapSolver: KCapHook = SolveCaps
) -> tuple[CappedShape, CageResult]:
    CheckSurface(Surface)
    Shape = CappedLayout(Surface)
    return Shape, ApplyStencil(BuildTable(Surface, CapSolver), Surface, Shape)


def ConvertCage(Surface: TsplineSurface, CapSolver: KCapHook = SolveCaps) -> CageResult:
    return CageParts(Surface, CapSolver)[1]
