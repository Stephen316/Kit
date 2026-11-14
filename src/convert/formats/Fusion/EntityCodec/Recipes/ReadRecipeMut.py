from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.formats.Fusion.EntityCodec.Recipes.ReadNodeMut import ReadNodeMut
from convert.formats.Fusion.EntityCodec.Recipes.ReadTagsMut import ReadTagsMut
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


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
