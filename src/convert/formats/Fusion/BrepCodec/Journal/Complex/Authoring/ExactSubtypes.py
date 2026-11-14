from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KSubtypeValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    CurveContext,
    ExactIntCur,
    ExpParCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    ExactSplSur,
    SplineCommon,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TreeParts import KBreaks

KEmptyRange = (1.0, 0.0)

KNullSurface = ChoiceValue("null_surface", ())

KNoBreaks: KBreaks = ((), (), ())


def ExactSurface(Surface: BsSurface) -> SubtypeNode:
    CheckBsSurface(Surface)
    Common = SplineCommon(Surface, 0.0, KNoBreaks, KNoBreaks)
    Record = ExactSplSur(23100, Common, KEmptyRange, KEmptyRange, 0)
    return SubtypeNode("exact_spl_sur", Record)


def ExactCurve(Curve: BsCurve) -> SubtypeNode:
    CheckBsCurve(Curve, 3)
    Context = CurveContext(
        23100,
        Curve,
        0.0,
        KNullSurface,
        KNullSurface,
        None,
        None,
        (None, None),
        KNoBreaks,
        0,
    )
    return SubtypeNode("exact_int_cur", ExactIntCur(Context, KEmptyRange, 0, 0))


def ParamCurve(Curve: BsCurve, SurfaceIndex: int) -> SubtypeNode:
    CheckBsCurve(Curve, 2)
    if type(SurfaceIndex) is not int or SurfaceIndex < 0:
        raise ValueError("Fusion pcurve surface reference must be a table index")
    Carrier = ChoiceValue(
        "spline",
        (False, SubtypeRef("surface", SurfaceIndex), (None, None, None, None)),
    )
    return SubtypeNode("exp_par_cur", ExpParCur(Curve, 0.0, Carrier))


def SplineSurface(Value: KSubtypeValue) -> BsSurface:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exact_spl_sur":
        if isinstance(Value.Body, ExactSplSur):
            return Value.Body.Common.ApproxSurface
    raise ValueError("Fusion surface is not an exact B-spline surface")


def SplineCurve(Value: KSubtypeValue) -> BsCurve:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exact_int_cur":
        if isinstance(Value.Body, ExactIntCur):
            return Value.Body.Context.ApproxCurve
    raise ValueError("Fusion curve is not an exact B-spline curve")


def PcurveSpline(Value: KSubtypeValue) -> BsCurve:
    if isinstance(Value, SubtypeNode) and Value.SubtypeName == "exp_par_cur":
        if isinstance(Value.Body, ExpParCur):
            return Value.Body.Spline
    raise ValueError("Fusion pcurve is not an explicit parameter-space B-spline")
