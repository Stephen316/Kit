from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.Formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the tags operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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
