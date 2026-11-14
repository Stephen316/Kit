from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    PickFace,
    PickVertex,
    RecipeTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CornerEdit import (
    CornerIndex,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue

KStackTolerance = 1e-9


def CornerWalls(
    Solid: PrismSolid, CornerCm: tuple[float, float]
) -> tuple[FaceLabel, FaceLabel]:
    Found: set[tuple[FaceLabel, FaceLabel]] = set()
    for SlabValue in Solid.Slabs:
        Matches = [
            (LoopValue[Index].Label, LoopValue[(Index + 1) % len(LoopValue)].Label)
            for LoopValue in SlabValue.Loops
            if (Index := CornerIndex(LoopValue, CornerCm)) is not None
        ]
        if len(Matches) != 1:
            raise ValueError("Fusion work geometry needs one vertical body edge")
        Found.add(Matches[0])
    IsStacked = all(
        abs(Lower.UpperCm - Upper.LowerCm) < KStackTolerance
        for Lower, Upper in zip(Solid.Slabs, Solid.Slabs[1:])
    )
    if len(Found) != 1 or not IsStacked:
        raise ValueError("Fusion work geometry needs one vertical body edge")
    return next(iter(Found))


def AxisRecipe(Solid: PrismSolid, CornerCm: tuple[float, float]) -> RecipeValue:
    Incoming, Outgoing = CornerWalls(Solid, CornerCm)
    Labels = [
        Incoming,
        Outgoing,
        Solid.Slabs[0].FloorLabel,
        Solid.Slabs[-1].RoofLabel,
    ]
    Payload = EdgeRecipe(
        -1,
        -1,
        (PickFace(0), PickFace(1)),
        (PickVertex((1, 0, 2)), PickVertex((1, 3, 0))),
        0,
    )
    return RecipeValue(3, RecipeTags(Labels), (), Payload)


def PointRecipe(Solid: PrismSolid, CornerCm: tuple[float, float]) -> RecipeValue:
    Incoming, Outgoing = CornerWalls(Solid, CornerCm)
    Labels = [Solid.Slabs[0].FloorLabel, Outgoing, Incoming]
    return RecipeValue(3, RecipeTags(Labels), (), PickVertex((1, 2, 0)))
