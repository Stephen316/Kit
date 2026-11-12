from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.RecipeRead import ReadRecipe
from tests.convert.formats.FusionParamTests import NativeText


# numeric naming components remain opaque and require their own zero terminator
def TestRecipeTerms() -> None:
    Header = bytes(2) + PackData("<IIII", 1, 3, 1, 1)
    TermValue = NativeText("axis", False) + PackData("<IIII", 3, 2, 305, 0xFFFFFECD)
    Suffix = bytes(4) + NativeText("edge_recipe_data", False) + b"\1\2\3"
    Valid = Header + TermValue + bytes(4) + Suffix
    assert ReadRecipe(MetaCursor(Valid)) == (
        "edge_recipe_data",
        ((("axis", 3, (305, 0xFFFFFECD)),),),
        b"\1\2\3",
    )
    Corrupt = Header + TermValue + PackData("<I", 1) + Suffix
    with Raises(ValueError, match="recipe term"):
        _ = ReadRecipe(MetaCursor(Corrupt))
