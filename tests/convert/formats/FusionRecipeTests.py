# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from struct import pack as Pack

from pytest import raises as Raises

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.RecipeRead import ReadRecipe
from tests.convert.formats.FusionParamTests import NativeText


# numeric naming components remain opaque and require their own zero terminator
def TestRecipeTerms() -> None:
    Header = bytes(2) + Pack("<IIII", 1, 3, 1, 1)
    Term = NativeText("axis", False) + Pack("<IIII", 3, 2, 305, 0xFFFFFECD)
    Suffix = bytes(4) + NativeText("edge_recipe_data", False) + b"\1\2\3"
    Valid = Header + Term + bytes(4) + Suffix
    assert ReadRecipe(MetaCursor(Valid)) == (
        "edge_recipe_data",
        ((("axis", 3, (305, 0xFFFFFECD)),),),
        b"\1\2\3",
    )
    Corrupt = Header + Term + Pack("<I", 1) + Suffix
    with Raises(ValueError, match="recipe term"):
        ReadRecipe(MetaCursor(Corrupt))
