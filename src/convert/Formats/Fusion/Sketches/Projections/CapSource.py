from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipes import KEdgeNames
from convert.Formats.Fusion.Topology.RecipeRead import KRecipeGuid


# context identity travels with the exact native recipe and typed boundary operands
@MakeDataClass(frozen=True, slots=True)
class CapSource:
    ContextId: int
    RecipeId: int
    Operands: KEdgeNames


# raw recipe equality is scoped to the already verified face context inventory
def IndexCapNames(
    BulkData: bytes, Owners: dict[int, RecordSpan], Recipe: FaceRecipePick
) -> dict[bytes, CapSource]:
    Index = {
        SelectCursor(BulkData, Owners, RecipeId, KRecipeGuid).DataValue: CapSource(
            ContextId, RecipeId, Operands
        )
        for ContextId, RecipeId, Operands in Recipe.ContextEdges
    }
    if len(Index) != 4:
        raise ValueError("Fusion cap source contexts have ambiguous recipe bytes")
    return Index
