from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.BlockSides import (
    SideUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormWindow,
)

KSideBoxes = (
    (0.0, 1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0, 1.0),
    (0.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 1.0),
)


@MakeDataClass(frozen=True, slots=True)
class EdgePlan:
    Maker: SideUse
    Users: tuple[SideUse, ...]


def EdgeKey(Graph: CageGraph, UseValue: SideUse) -> frozenset[int]:
    return frozenset(Graph.Links[Entry].EdgeIndex for Entry in UseValue.Links)


def PlanEdges(
    Graph: CageGraph, Loops: tuple[tuple[SideUse, ...], ...]
) -> tuple[EdgePlan, ...]:
    Makers: dict[frozenset[int], SideUse] = {}
    for UseValue in (Entry for LoopUses in Loops for Entry in LoopUses):
        _ = Makers.setdefault(EdgeKey(Graph, UseValue), UseValue)
    Users: dict[frozenset[int], list[SideUse]] = {}
    for LoopUses in reversed(Loops):
        for UseValue in LoopUses:
            Users.setdefault(EdgeKey(Graph, UseValue), []).append(UseValue)
    if any(len(Members) > 2 for Members in Users.values()):
        raise ValueError("Fusion Form capped layout found a non-manifold edge")
    return tuple(
        EdgePlan(Makers[UseKey], tuple(Members)) for UseKey, Members in Users.items()
    )


def PlanPoints(Plans: tuple[EdgePlan, ...]) -> tuple[int, ...]:
    Points: dict[int, int] = {}
    for PlanValue in Plans:
        _ = Points.setdefault(PlanValue.Maker.StartVertex, len(Points))
        _ = Points.setdefault(PlanValue.Maker.FinalVertex, len(Points))
    return tuple(Points)


def PlanRange(PlanValue: EdgePlan, Scale: int) -> tuple[float, float]:
    Maker = PlanValue.Maker
    Along = Maker.Side % 2
    Signum = 1.0 if Maker.Side < 2 else -1.0
    return (
        Signum * float(Maker.Start[Along] * Scale),
        Signum * float(Maker.Final[Along] * Scale),
    )


def IsWithin(Inner: SideUse, Outer: SideUse) -> bool:
    return Inner.Region == Outer.Region and set(Inner.Links) <= set(Outer.Links)


def WideUse(WidePlans: tuple[EdgePlan, ...], UseValue: SideUse) -> tuple[int, SideUse]:
    for PlanIndex, PlanValue in enumerate(WidePlans):
        for Entry in PlanValue.Users:
            if IsWithin(UseValue, Entry):
                return PlanIndex, Entry
    raise ValueError("Fusion Form capped layout found an edge outside every curve")


def EdgeBounds(
    PlanValue: EdgePlan, Outer: EdgePlan, Scale: int
) -> tuple[float, float] | None:
    for Inner in PlanValue.Users:
        if IsWithin(Inner, Outer.Maker):
            if Inner.Links == Outer.Maker.Links:
                return None
            return PlanRange(EdgePlan(Inner, ()), Scale)
    raise ValueError("Fusion Form capped layout found an edge off its curve")


def IsReversed(PlanValue: EdgePlan, UseValue: SideUse) -> bool:
    return UseValue.Links[0] not in PlanValue.Maker.Links


def UseTrace(PlanValue: EdgePlan, UseValue: SideUse, Scale: int) -> BsCurve:
    Start = (float(UseValue.Start[0] * Scale), float(UseValue.Start[1] * Scale))
    Final = (float(UseValue.Final[0] * Scale), float(UseValue.Final[1] * Scale))
    Poles = (Final, Start) if IsReversed(PlanValue, UseValue) else (Start, Final)
    Closure = PlanValue.Maker.Closure
    return BsCurve(False, 1, Closure, PlanRange(PlanValue, Scale), (1, 1), 2, Poles, ())


def IsSelfEdge(PlanValue: EdgePlan) -> bool:
    return len({UseValue.Region for UseValue in PlanValue.Users}) == 1


def SideWindow(FaceIndex: int, LocalSide: int, Scale: int) -> FormWindow:
    LowerU, UpperU, LowerV, UpperV = KSideBoxes[LocalSide]
    return FormWindow(
        FaceIndex, Scale * LowerU, Scale * UpperU, Scale * LowerV, Scale * UpperV
    )


def PlanWindows(PlanValue: EdgePlan, Scale: int) -> tuple[FormWindow, ...]:
    if not IsSelfEdge(PlanValue):
        return ()
    return tuple(
        SideWindow(FaceIndex, LocalSide, Scale)
        for UseValue in PlanValue.Users
        for FaceIndex, LocalSide in UseValue.Cells
    )


def PlanConvexity(Graph: CageGraph, PlanValue: EdgePlan) -> str:
    IsCreased = any(Graph.Creased[Entry] for Entry in PlanValue.Maker.Links)
    return "unknown" if len(PlanValue.Users) < 2 or IsCreased else "tangent"
