from math import hypot as Hypot

from convert.adapters.freecad.EditRead.Sketch.RuleOperands import (
    KSketchAngleTol,
    KSketchRuleTol,
    PointDelta,
    RuleCircle,
    RuleLine,
    RuleLineAxis,
    RuleLineLocal,
    RuleOperand,
    RulePoint,
)
from convert.adapters.freecad.EditRead.Sketch.RuleTangent import TangentBranch
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# finite physical distances make point residuals independent of coordinate signs
def IsSameSketchPt(First: PlaneVector, Second: PlaneVector) -> bool:
    Delta = PointDelta(First, Second)
    return Hypot(Delta.x, Delta.y) <= KSketchRuleTol


# point on object validates the exact finite segment or entire circular carrier
def IsPointOnCurve(First: RuleOperand, Second: RuleOperand) -> bool:
    Point = RulePoint(First)
    if isinstance(Second.Geometry, LineGeometry):
        Along, Offset, Length = RuleLineLocal(Point, RuleLine(Second))
        return (
            abs(Offset) <= KSketchRuleTol
            and -KSketchRuleTol <= Along <= Length + KSketchRuleTol
        )
    Circle = RuleCircle(Second)
    Delta = PointDelta(Circle.center, Point)
    return abs(Hypot(Delta.x, Delta.y) - Circle.radius) <= KSketchRuleTol


# line pairs use normalized direction tests or a physical length comparison
def IsLineRelation(KindValue: str, First: RuleOperand, Second: RuleOperand) -> bool:
    AxisA, LengthA = RuleLineAxis(RuleLine(First))
    AxisB, LengthB = RuleLineAxis(RuleLine(Second))
    if KindValue == "parallel":
        return abs(AxisA.x * AxisB.y - AxisA.y * AxisB.x) <= KSketchAngleTol
    if KindValue == "perpendicular":
        return abs(AxisA.x * AxisB.x + AxisA.y * AxisB.y) <= KSketchAngleTol
    return abs(LengthA - LengthB) <= KSketchRuleTol


# basic binary relations must remain solved on their authored operands
def IsBinaryRule(KindValue: str, First: RuleOperand, Second: RuleOperand) -> bool:
    if KindValue in ("horizontal", "vertical"):
        Delta = PointDelta(RulePoint(First), RulePoint(Second))
        return abs(Delta.y if KindValue == "horizontal" else Delta.x) <= KSketchRuleTol
    if KindValue == "coincident":
        return IsSameSketchPt(RulePoint(First), RulePoint(Second))
    if KindValue == "point_on_object":
        return IsPointOnCurve(First, Second)
    if KindValue == "midpoint":
        Segment = RuleLine(Second)
        Direction, Length = RuleLineAxis(Segment)
        Expected = PlaneVector(
            Segment.start.x + Direction.x * Length / 2.0,
            Segment.start.y + Direction.y * Length / 2.0,
        )
        return IsSameSketchPt(RulePoint(First), Expected)
    if KindValue == "concentric":
        return IsSameSketchPt(RuleCircle(First).center, RuleCircle(Second).center)
    if KindValue == "equal" and isinstance(First.Geometry, CircleGeometry):
        return (
            abs(RuleCircle(First).radius - RuleCircle(Second).radius) <= KSketchRuleTol
        )
    if KindValue in ("parallel", "perpendicular", "equal"):
        return IsLineRelation(KindValue, First, Second)
    return False


# reflecting the first point across the authored axis reproduces the second point
def IsSketchSymm(Operands: tuple[RuleOperand, ...]) -> bool:
    First, Second, Third = Operands
    Point = RulePoint(First)
    Segment = RuleLine(Third)
    Direction, _ = RuleLineAxis(Segment)
    _, Offset, _ = RuleLineLocal(Point, Segment)
    Expected = PlaneVector(
        Point.x + 2.0 * Direction.y * Offset,
        Point.y - 2.0 * Direction.x * Offset,
    )
    return IsSameSketchPt(Expected, RulePoint(Second))


# supported authored geometric constraints must hold after applying edited coordinates
def CheckGeomRule(
    KindValue: str, Original: tuple[RuleOperand, ...], Edited: tuple[RuleOperand, ...]
) -> None:
    if KindValue == "tangent":
        Matches = TangentBranch(Original) == TangentBranch(Edited)
    elif len(Edited) == 1 and KindValue in ("horizontal", "vertical"):
        Direction, Length = RuleLineAxis(RuleLine(Edited[0]))
        Residual = Direction.y if KindValue == "horizontal" else Direction.x
        Matches = abs(Residual * Length) <= KSketchRuleTol
    elif len(Edited) == 2:
        Matches = IsBinaryRule(KindValue, Edited[0], Edited[1])
    elif len(Edited) == 3 and KindValue == "symmetric":
        Matches = IsSketchSymm(Edited)
    else:
        Matches = False
    if not Matches:
        raise ValueError(
            f"FreeCAD editable sketch {KindValue} constraint residual changed"
        )
