from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundChain import (
    FindSeed,
    ShapeUsers,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundFrame import (
    CapNormal,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundPlan import (
    ChainLink,
    PlanRound,
    RoundPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    CrossProduct,
    DotProduct,
    IsSamePoint,
    KSpaceVector,
    SubVector,
    UnitVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan

KTurnLimit = 1e-9


def ChainPlans(Shape: ShapeBody, Points: tuple[KSpaceVector, ...]) -> list[RoundPlan]:
    Users = ShapeUsers(Shape)
    Plans: list[RoundPlan] = []
    Taken: set[tuple[int, int, int]] = set()
    LabelBase = 0
    for PointCm in Points:
        PlanValue = PlanRound(Shape, Users, FindSeed(Shape, PointCm))
        for LinkValue in PlanValue.Links:
            Place = (PlanValue.CapIndex, PlanValue.LoopIndex, LinkValue.UseIndex)
            if Place in Taken:
                raise ValueError("Fusion edge rounds need distinct edges")
            Taken.add(Place)
        Numbers = tuple(LabelBase + Number for Number in PlanValue.Numbers)
        Plans.append(ReplaceValue(PlanValue, Numbers=Numbers))
        LabelBase += len(PlanValue.Links)
    return Plans


def IsStraight(Shape: ShapeBody, LinkValue: ChainLink) -> bool:
    WallValue = Shape.Faces[LinkValue.WallIndex]
    return isinstance(WallValue, WallFace) and isinstance(WallValue.Span, LineSpan)


def IsMitre(
    Shape: ShapeBody, PlanValue: RoundPlan, Before: ChainLink, After: ChainLink
) -> bool:
    CapValue = Shape.Faces[PlanValue.CapIndex]
    if PlanValue.Sense < 0 or not isinstance(CapValue, CapFace):
        return False
    if not IsStraight(Shape, Before) or not IsStraight(Shape, After):
        return False
    if not IsSamePoint(Before.Finish, After.Start):
        return False
    Leading = UnitVector(SubVector(Before.Finish, Before.Start))
    Trailing = UnitVector(SubVector(After.Finish, After.Start))
    Turning = DotProduct(CrossProduct(Leading, Trailing), CapNormal(CapValue))
    return Turning > KTurnLimit


def CanFollow(Shape: ShapeBody, First: RoundPlan, Second: RoundPlan) -> bool:
    if (First.CapIndex, First.LoopIndex) != (Second.CapIndex, Second.LoopIndex):
        return False
    if First.Closed or Second.Closed or First.Sense != Second.Sense:
        return False
    Count = len(Shape.Faces[First.CapIndex].Loops[First.LoopIndex])
    if (First.Links[-1].UseIndex + 1) % Count != Second.Links[0].UseIndex:
        return False
    return IsMitre(Shape, First, First.Links[-1], Second.Links[0])


def JoinPlans(First: RoundPlan, Second: RoundPlan) -> RoundPlan:
    return ReplaceValue(
        First,
        Links=(*First.Links, *Second.Links),
        Numbers=(*First.Numbers, *Second.Numbers),
        Mitres=(*First.Mitres[:-1], True, *Second.Mitres[1:]),
    )


def ClosePlan(Shape: ShapeBody, PlanValue: RoundPlan) -> RoundPlan:
    if not CanFollow(Shape, PlanValue, PlanValue):
        return PlanValue
    Mitres = (True, *PlanValue.Mitres[1:-1])
    return ReplaceValue(PlanValue, Closed=True, Mitres=Mitres)


def CanMergeMut(Shape: ShapeBody, Plans: list[RoundPlan]) -> bool:
    for First in Plans:
        for Second in Plans:
            if First is Second or not CanFollow(Shape, First, Second):
                continue
            Plans[Plans.index(First)] = JoinPlans(First, Second)
            Plans.remove(Second)
            return True
    return False


def GroupPlans(Shape: ShapeBody, Points: tuple[KSpaceVector, ...]) -> list[RoundPlan]:
    Plans = ChainPlans(Shape, Points)
    while CanMergeMut(Shape, Plans):
        continue
    Closed = [ClosePlan(Shape, PlanValue) for PlanValue in Plans]
    return sorted(Closed, key=lambda PlanValue: min(PlanValue.Numbers))


def IsWithCap(
    Shape: ShapeBody,
    PlanValue: RoundPlan,
    LinkValue: ChainLink,
    Blends: tuple[FaceLabel, ...],
) -> bool:
    CapValue = Shape.Faces[PlanValue.CapIndex]
    EdgeValue = CapValue.Loops[PlanValue.LoopIndex][LinkValue.UseIndex].Edge
    if isinstance(EdgeValue, LevelEdge) and EdgeValue.Span.Label in Blends:
        return False
    return isinstance(CapValue, CapFace) and CapNormal(CapValue)[2] > 0.0


def PlanLegs(Shape: ShapeBody, PlanValue: RoundPlan, Round: EdgeRound) -> EdgeRound:
    SeedLink = PlanValue.Links[PlanValue.Numbers.index(min(PlanValue.Numbers))]
    if IsWithCap(Shape, PlanValue, SeedLink, Round.Blends):
        return Round
    return ReplaceValue(Round, CapCm=Round.WallCm, WallCm=Round.CapCm)
