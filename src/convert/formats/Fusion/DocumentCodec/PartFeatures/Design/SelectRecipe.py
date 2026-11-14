from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    LabelGroups,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanFinish
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe


def RecipeTags(Labels: list[FaceLabel]) -> tuple[tuple[RecipeTag, ...], ...]:
    return tuple(
        tuple(
            RecipeTag(
                tuple(Group.PrimaryId.encode("ascii")),
                Group.SecondaryId,
                Group.OperationIds,
                0,
            )
            for Group in LabelGroups(Label)
        )
        for Label in Labels
    )


def PickFace(Index: int) -> FaceRecipe:
    return FaceRecipe(Index, -1)


def PickVertex(Indices: tuple[int, ...]) -> VertexRecipe[EdgeRecipe]:
    return VertexRecipe(-1, tuple(PickFace(Index) for Index in Indices), (), ())


def CornerRecipe(Solid: PrismSolid, CornerCm: tuple[float, float]) -> RecipeValue:
    LoopValue = next(
        LoopValue
        for LoopValue in Solid.Slabs[0].Loops
        for Value in LoopValue
        if abs(SpanFinish(Value)[0] - CornerCm[0]) < 1e-7
        and abs(SpanFinish(Value)[1] - CornerCm[1]) < 1e-7
    )
    Index = next(
        Index
        for Index, Value in enumerate(LoopValue)
        if abs(SpanFinish(Value)[0] - CornerCm[0]) < 1e-7
        and abs(SpanFinish(Value)[1] - CornerCm[1]) < 1e-7
    )
    Labels = [
        LoopValue[Index].Label,
        LoopValue[(Index + 1) % len(LoopValue)].Label,
        Solid.Slabs[0].FloorLabel,
        Solid.Slabs[-1].RoofLabel,
    ]
    Payload = EdgeRecipe(
        -1,
        -1,
        (PickFace(0), PickFace(1)),
        (PickVertex((1, 0, 2)), PickVertex((1, 3, 0))),
        -1,
    )
    return RecipeValue(3, RecipeTags(Labels), (), Payload)
