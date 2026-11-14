from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    PickFace,
    PickVertex,
    RecipeTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe

KRimOrders = (UvOrderEntry(0, UvOrder(2, 2, 2, 2, 1, 0, 1)),)
KSidePlans = (
    ((0, 1), (0, 2, 1), (3, 0, 1)),
    ((0, 3), (3, 0, 1), (3, 4, 0)),
    ((0, 4), (0, 4, 2), (3, 4, 0)),
    ((2, 0), (0, 2, 1), (0, 4, 2)),
)


def SideRecipe(Solid: PrismSolid, Index: int) -> RecipeValue:
    SlabValue = Solid.Slabs[-1]
    LoopValue = SlabValue.Loops[0]
    Labels = [
        LoopValue[Index].Label,
        Solid.Slabs[0].FloorLabel,
        LoopValue[Index - 1].Label,
        LoopValue[(Index + 1) % len(LoopValue)].Label,
        SlabValue.RoofLabel,
    ]
    Edges = tuple(
        EdgeRecipe(
            -1,
            -1,
            tuple(PickFace(Place) for Place in Faces),
            (PickVertex(Opening), PickVertex(Closing)),
            -1,
        )
        for Faces, Opening, Closing in KSidePlans
    )
    return RecipeValue(3, RecipeTags(Labels), (), BoundFaceRecipe(0, -1, Edges))


def RoofPlans(Solid: PrismSolid) -> list[tuple[tuple[FaceLabel, ...], ...]]:
    Ceiling = Solid.Slabs[-1]
    LoopValue = next(Value for Value in Ceiling.Loops if LoopArea(Value) > 0)
    RoofValue = Ceiling.RoofLabel
    Order = (LoopValue[-1], *LoopValue[:-1])
    First = (Order[-1].Label, Order[0].Label, RoofValue)
    Opening = First
    Plans: list[tuple[tuple[FaceLabel, ...], ...]] = []
    for Index, Value in enumerate(Order):
        Closing = (
            First
            if Index + 1 == len(Order)
            else (Order[Index + 1].Label, RoofValue, Value.Label)
        )
        Plans.append(((Value.Label, RoofValue), Opening, Closing))
        Opening = Closing
    return Plans


def RimRecipe(Solid: PrismSolid, WallLabel: FaceLabel) -> RecipeValue:
    Ceiling = Solid.Slabs[-1]
    RimLabels = [
        RimLabel
        for Owner, Level, RimLabel in Solid.EdgeTags
        if Owner == WallLabel and abs(Level - Ceiling.UpperCm) < 1e-9
    ]
    if not RimLabels:
        raise ValueError("Fusion circular roofs require a tagged top edge")
    Sides = (PickFace(2), PickFace(0))
    Loose = EdgeRecipe(1, -1, (), (), -1)
    Corner = VertexRecipe(-1, Sides, (Loose,), KRimOrders)
    Payload = BoundFaceRecipe(0, -1, (EdgeRecipe(1, -1, Sides, (Corner,), -1),))
    return RecipeValue(
        3, RecipeTags([Ceiling.RoofLabel, RimLabels[0], WallLabel]), (), Payload
    )


def RoofRecipe(Solid: PrismSolid) -> RecipeValue:
    Ceiling = Solid.Slabs[-1]
    LoopValue = next(Value for Value in Ceiling.Loops if LoopArea(Value) > 0)
    if len(LoopValue) == 1 and IsFullCircle(LoopValue[0]):
        return RimRecipe(Solid, LoopValue[0].Label)
    Plans = RoofPlans(Solid)
    Labels: list[FaceLabel] = [Solid.Slabs[-1].RoofLabel]
    for PlanValue in Plans:
        Labels.extend(
            Label for Group in PlanValue for Label in Group if Label not in Labels
        )
    Place = {Label: Index for Index, Label in enumerate(Labels)}
    Edges = tuple(
        EdgeRecipe(
            -1,
            -1,
            tuple(PickFace(Place[Label]) for Label in Faces),
            (
                PickVertex(tuple(Place[Label] for Label in Opening)),
                PickVertex(tuple(Place[Label] for Label in Closing)),
            ),
            -1,
        )
        for Faces, Opening, Closing in Plans
    )
    return RecipeValue(3, RecipeTags(Labels), (), BoundFaceRecipe(0, -1, Edges))


def RoofFaceRecipe(Solid: PrismSolid) -> RecipeValue:
    Labels = [Solid.Slabs[-1].RoofLabel]
    return RecipeValue(3, RecipeTags(Labels), (), PickFace(0))
