from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Added,
    BaseFrame,
    ChildFrame,
    DotProduct,
    Scaled,
    ViewFrame,
)

# the point pair shape must stay shared so drawing view authoring uses one contract for compatible values
KPointPair = tuple[float, float]

# the point triple shape must stay shared so drawing view authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]

# border margin must remain consistent across callers so projected geometry retains its paper and model relationships
KBorderMargin = 3.25

# unit scale must remain consistent across callers so projected geometry retains its paper and model relationships
KUnitScale = 10.0

# model origin must remain consistent across callers so projected geometry retains its paper and model relationships
KModelOrigin = -10000.0

# model spacing must remain consistent across callers so projected geometry retains its paper and model relationships
KModelSpacing = 1000.0


# view plan needs an explicit state contract so projected geometry retains its paper and model relationships
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


# the spread contract needs a shared interpretation so projected geometry retains its paper and model relationships
def Spread(Frame: ViewFrame, Extent: KPointTriple) -> KPointPair:
    Across = sum(abs(AxisPart) * Paper for AxisPart, Paper in zip(Frame.Right, Extent))
    Upward = sum(abs(AxisPart) * Paper for AxisPart, Paper in zip(Frame.Up, Extent))
    return (Across, Upward)


# the plan view contract needs a stable decomposition so projected geometry retains its paper and model relationships
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


# the plan views contract needs a stable decomposition so projected geometry retains its paper and model relationships
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
