from dataclasses import dataclass as MakeDataClass
from math import atan2 as ArcTangent
from math import pi as KHalfTurn
from math import sqrt as SquareRoot

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft

KPointPair = tuple[float, float]
KPointTriple = tuple[float, float, float]
KTolerance = 1e-9
KBaseKind = 4
KProjectedKind = 0


@MakeDataClass(frozen=True, slots=True)
class ViewFrame:
    Eye: KPointTriple
    Up: KPointTriple
    Right: KPointTriple
    ViewScale: float
    ViewKind: int
    ViewAngle: float


def Cross(First: KPointTriple, Second: KPointTriple) -> KPointTriple:
    return (
        First[1] * Second[2] - First[2] * Second[1],
        First[2] * Second[0] - First[0] * Second[2],
        First[0] * Second[1] - First[1] * Second[0],
    )


def DotProduct(First: KPointTriple, Second: KPointTriple) -> float:
    return sum(Former * Right for Former, Right in zip(First, Second))


def Scaled(Vector: KPointTriple, Factor: float) -> KPointTriple:
    return (Vector[0] * Factor, Vector[1] * Factor, Vector[2] * Factor)


def Added(First: KPointTriple, Second: KPointTriple) -> KPointTriple:
    return (First[0] + Second[0], First[1] + Second[1], First[2] + Second[2])


def IsUnit(Vector: KPointTriple) -> bool:
    return abs(SquareRoot(DotProduct(Vector, Vector)) - 1) < KTolerance


def IsAxis(Vector: KPointTriple) -> bool:
    return sum(abs(Component) > KTolerance for Component in Vector) == 1


def BaseFrame(Draft: ViewDraft) -> ViewFrame:
    if not IsUnit(Draft.EyeDirection) or not IsUnit(Draft.UpVector):
        raise ValueError("Authored DWG view directions must be unit vectors")
    if not IsAxis(Draft.EyeDirection) or not IsAxis(Draft.UpVector):
        raise ValueError("Authored DWG base views must look along a model axis")
    if abs(DotProduct(Draft.EyeDirection, Draft.UpVector)) > KTolerance:
        raise ValueError("Authored DWG view up vector must be normal to its eye")
    if Draft.ViewScale <= 0:
        raise ValueError("Authored DWG view scale must be positive")
    Right = Cross(Draft.UpVector, Draft.EyeDirection)
    return ViewFrame(
        Draft.EyeDirection, Draft.UpVector, Right, Draft.ViewScale, KBaseKind, 0.0
    )


def ChildFrame(Parent: ViewFrame, Offset: KPointPair) -> ViewFrame:
    Across, Upward = Offset
    if abs(Upward) < KTolerance and abs(Across) > KTolerance:
        Signum = 1.0 if Across > 0 else -1.0
        EyeAxis = Scaled(Parent.Right, -Signum)
        UpAxis = Parent.Up
    elif abs(Across) < KTolerance and abs(Upward) > KTolerance:
        Signum = 1.0 if Upward > 0 else -1.0
        EyeAxis = Scaled(Parent.Up, -Signum)
        UpAxis = Scaled(Parent.Eye, Signum)
    else:
        raise ValueError(
            "Authored DWG projected view must sit beside or above its parent"
        )
    Angle = ArcTangent(Upward, Across) % (2 * KHalfTurn)
    return ViewFrame(
        EyeAxis, UpAxis, Cross(UpAxis, EyeAxis), Parent.ViewScale, KProjectedKind, Angle
    )


def TwistAngle(Frame: ViewFrame) -> float:
    Normal = Frame.Eye
    IsPolar = max(abs(Normal[0]), abs(Normal[1])) < 1 / 64
    AxisPart = Cross((0.0, 1.0, 0.0) if IsPolar else (0.0, 0.0, 1.0), Normal)
    AxisPart = Scaled(AxisPart, 1 / SquareRoot(DotProduct(AxisPart, AxisPart)))
    Other = Cross(Normal, AxisPart)
    Angle = ArcTangent(
        DotProduct(Frame.Right, Other), DotProduct(Frame.Right, AxisPart)
    )
    return (-Angle) % (2 * KHalfTurn)
