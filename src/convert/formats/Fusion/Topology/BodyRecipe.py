# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.RecipeRead import KRecipeGuid, ReadRecipe

# body recipe names are opaque and never supply the selected native body identity
KBodyRecipe = "body_recipe_data"


# the observed whole body recipe is independent of its explicit native anchor
def ReadBodyRecipe(
    BulkData: bytes, Owners: dict[int, RecordSpan], RecipeId: int
) -> str:
    Cursor = SelectCursor(BulkData, Owners, RecipeId, KRecipeGuid)
    if len(Cursor.DataValue) > 256:
        raise ValueError("Oversized Fusion whole body recipe")
    KindValue, Terms, Payload = ReadRecipe(Cursor)
    if (
        KindValue != KBodyRecipe
        or len(Terms) != 1
        or len(Terms[0]) != 1
        or Terms[0][0][1] not in (4, 7)
        or Terms[0][0][2]
        or Payload != b"\0\0\0\0\xff\xff\xff\xff"
    ):
        raise ValueError("Unsupported Fusion whole body recipe")
    return Terms[0][0][0]
