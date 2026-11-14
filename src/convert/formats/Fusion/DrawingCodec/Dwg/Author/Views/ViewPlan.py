from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Added,
    BaseFrame,
    ChildFrame,
    DotProduct,
    Scaled,
    ViewFrame,
)

KPointPair = tuple[float, float]
KPointTriple = tuple[float, float, float]
KBorderMargin = 3.25
KUnitScale = 10.0
KModelOrigin = -10000.0
KModelSpacing = 1000.0


@MakeDataClass(frozen=True, slots=True)
class ViewPlan:
    Index: int
    Parent: int
    Frame: ViewFrame
    Center: KPointPair
    BorderSize: KPointPair
    Insertion: KPointTriple
    Target: KPointTriple
    TargetPoint: KPointTriple
    EyePoint: KPointTriple
    Extent: KPointTriple
    ShowHidden: bool


def Spread(Frame: ViewFrame, Extent: KPointTriple) -> KPointPair:
    Across = sum(abs(AxisPart) * Paper for AxisPart, Paper in zip(Frame.Right, Extent))
    Upward = sum(abs(AxisPart) * Paper for AxisPart, Paper in zip(Frame.Up, Extent))
    return (Across, Upward)


def PlanView(
    Index: int,
    Draft: ViewDraft,
    Frame: ViewFrame,
    Source: ViewSource,
    Sheet: KPointPair,
) -> ViewPlan:
    Extent = tuple(
        Upper - Lower for Lower, Upper in zip(Source.BoundsMin, Source.BoundsMax)
    )
    Paper: KPointTriple = (Extent[0], Extent[1], Extent[2])
    Middle = Scaled(Added(Source.BoundsMin, Source.BoundsMax), 0.5)
    Across, Upward = Spread(Frame, Paper)
    Border = (
        Across * KUnitScale * Frame.ViewScale + 2 * KBorderMargin,
        Upward * KUnitScale * Frame.ViewScale + 2 * KBorderMargin,
    )
    Insertion = (
        KModelOrigin + Sheet[0] / 2 + Index * KModelSpacing,
        KModelOrigin + Sheet[1] / 2,
        0.0,
    )
    Reach = max(Paper) if max(Paper) > 0 else 1.0
    return ViewPlan(
        Index,
        Draft.Parent,
        Frame,
        Draft.Center,
        Border,
        Insertion,
        Added(Insertion, Scaled(Middle, KUnitScale)),
        Middle,
        Added(Middle, Scaled(Frame.Eye, Reach)),
        Paper,
        Draft.ShowHidden,
    )


def PlanViews(
    Drafts: tuple[ViewDraft, ...], Source: ViewSource, Sheet: KPointPair
) -> tuple[ViewPlan, ...]:
    Plans: list[ViewPlan] = []
    for Index, Draft in enumerate(Drafts):
        if Draft.Parent >= Index:
            raise ValueError("Authored DWG projected view must follow its parent")
        if Draft.Parent < 0:
            Frame = BaseFrame(Draft)
        else:
            Parent = Plans[Draft.Parent]
            if Draft.ShowHidden != Parent.ShowHidden:
                raise ValueError(
                    "Authored DWG projected view must show hidden edges as its parent"
                )
            Offset = (
                Draft.Center[0] - Parent.Center[0],
                Draft.Center[1] - Parent.Center[1],
            )
            Frame = ChildFrame(Parent.Frame, Offset)
        Plans.append(PlanView(Index, Draft, Frame, Source, Sheet))
    if any(
        abs(DotProduct(Planned.Frame.Eye, Planned.Frame.Up)) > 1e-9 for Planned in Plans
    ):
        raise ValueError("Authored DWG view frame is not orthogonal")
    return tuple(Plans)
