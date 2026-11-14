from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeCurves import LineEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundChain import KUsePlace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import (
    CornerFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundFrame import UseEnds
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    DotProduct,
    IsSamePoint,
    KSpaceVector,
    ScaleVector,
    SubVector,
    UnitVector,
    VectorLength,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import (
    EdgeCurve,
    EdgeEnds,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import (
    KShapeEdge,
    ShapeUse,
)

KSquareLimit = 1e-9


def TrimEdge(
    EdgeValue: KShapeEdge, Point: KSpaceVector, Target: KSpaceVector
) -> FreeEdge:
    Curve, _, _ = EdgeCurve(EdgeValue)
    if not isinstance(Curve, StraightNode):
        raise ValueError("Fusion edge rounds need straight neighbouring edges")
    Start, Finish = EdgeEnds(EdgeValue)
    if IsSamePoint(Start, Point):
        Trimmed = LineEdge(Target, Finish)
    elif IsSamePoint(Finish, Point):
        Trimmed = LineEdge(Start, Target)
    else:
        raise ValueError("Fusion edge round neighbours must meet the rounded edge")
    Heading = UnitVector(SubVector(Finish, Start))
    KeptCosine = DotProduct(
        Heading, UnitVector(SubVector(Trimmed.FinishCm, Trimmed.StartCm))
    )
    Offset = SubVector(Target, Start)
    GapLength = VectorLength(
        SubVector(Offset, ScaleVector(Heading, DotProduct(Offset, Heading)))
    )
    if KeptCosine < 1.0 - KSquareLimit or GapLength > 1e-7:
        raise ValueError("Fusion edge rounds need square neighbouring edges")
    return Trimmed


def JointEdge(
    Users: dict[KShapeEdge, list[KUsePlace]], Faces: set[int], Point: KSpaceVector
) -> KShapeEdge:
    for EdgeValue, Places in Users.items():
        if {Place[0] for Place in Places} != Faces:
            continue
        if any(IsSamePoint(EndPoint, Point) for EndPoint in EdgeEnds(EdgeValue)):
            return EdgeValue
    raise ValueError("Fusion edge round corners need three meeting faces")


def CrossForward(
    Arrive: KSpaceVector, Leave: KSpaceVector, Frame: CornerFrame
) -> bool | None:
    if IsSamePoint(Arrive, Frame.CapPoint) and IsSamePoint(Leave, Frame.WallPoint):
        return True
    if IsSamePoint(Arrive, Frame.WallPoint) and IsSamePoint(Leave, Frame.CapPoint):
        return False
    return None


def InsertCross(
    FaceValue: KShapeFace, Frame: CornerFrame, Cross: FreeEdge
) -> KShapeFace:
    Loops = FaceValue.Loops
    for LoopIndex, LoopValue in enumerate(Loops):
        for Index, UseValue in enumerate(LoopValue):
            Following = LoopValue[(Index + 1) % len(LoopValue)]
            Forward = CrossForward(UseEnds(UseValue)[1], UseEnds(Following)[0], Frame)
            if Forward is None:
                continue
            Grown = (
                *LoopValue[: Index + 1],
                ShapeUse(Cross, Forward),
                *LoopValue[Index + 1 :],
            )
            Changed = (*Loops[:LoopIndex], Grown, *Loops[LoopIndex + 1 :])
            return ReplaceValue(FaceValue, Loops=Changed)
    raise ValueError("Fusion edge round end faces must meet the round")


def SwapFaces(
    Faces: tuple[KShapeFace, ...],
    Swaps: dict[KShapeEdge, KShapeEdge],
    Replace: dict[tuple[int, KShapeEdge], ShapeUse],
) -> list[KShapeFace]:
    Result: list[KShapeFace] = []
    for FaceIndex, FaceValue in enumerate(Faces):
        Loops: list[tuple[ShapeUse, ...]] = []
        for LoopValue in FaceValue.Loops:
            UseList: list[ShapeUse] = []
            for UseValue in LoopValue:
                Swapped = Swaps.get(UseValue.Edge)
                Chosen = Replace.get((FaceIndex, UseValue.Edge))
                if Chosen is None and Swapped is not None:
                    Chosen = ShapeUse(Swapped, UseValue.Forward)
                UseList.append(UseValue if Chosen is None else Chosen)
            Loops.append(tuple(UseList))
        Result.append(ReplaceValue(FaceValue, Loops=tuple(Loops)))
    return Result
