from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadTagsMut(
    Cursor: MetaCursor, Catalog: EntityCatalog
) -> tuple[tuple[RecipeTag, ...], ...]:
    Groups: list[tuple[RecipeTag, ...]] = []
    for _ in range(ReadCountMut(Cursor, Catalog)):
        TagRows: list[RecipeTag] = []
        for _ in range(ReadCountMut(Cursor, Catalog)):
            PrimaryId = tuple(Cursor.TakeBytes(ReadCountMut(Cursor, Catalog)))
            SecondaryId = int(ReadAtomMut(Cursor, WireType("i32")))
            Operations = tuple(
                int(ReadAtomMut(Cursor, WireType("i32")))
                for _ in range(ReadCountMut(Cursor, Catalog))
            )
            ApproachId = int(ReadAtomMut(Cursor, WireType("i32")))
            TagRows.append(RecipeTag(PrimaryId, SecondaryId, Operations, ApproachId))
        Groups.append(tuple(TagRows))
    return tuple(Groups)
