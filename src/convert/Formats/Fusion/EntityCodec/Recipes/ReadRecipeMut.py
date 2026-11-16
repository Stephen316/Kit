from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.Formats.Fusion.EntityCodec.Recipes.ReadNodeMut import ReadNodeMut
from convert.Formats.Fusion.EntityCodec.Recipes.ReadTagsMut import ReadTagsMut
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the recipe operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadRecipeMut(
    Cursor: MetaCursor, Catalog: EntityCatalog, Depth: int
) -> RecipeValue:
    Version = int(ReadAtomMut(Cursor, WireType("i32")))
    if Version != 3:
        raise ValueError("Only Fusion ASM recipe version three is qualified")
    TagRows = ReadTagsMut(Cursor, Catalog)
    LwdTags = ReadTagsMut(Cursor, Catalog)
    KindValue = Cursor.TakeBytes(ReadCountMut(Cursor, Catalog)).decode("ascii")
    return RecipeValue(
        Version, TagRows, LwdTags, ReadNodeMut(Cursor, KindValue, Catalog, Depth + 1)
    )
