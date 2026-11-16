from convert.Formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder
from convert.Formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry
from convert.Formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the uv orders operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadUvOrdersMut(
    Cursor: MetaCursor, Catalog: EntityCatalog
) -> tuple[UvOrderEntry, ...]:
    Entries: list[UvOrderEntry] = []
    KeySet: set[int] = set()
    for _ in range(ReadCountMut(Cursor, Catalog)):
        KeyValue = int(ReadAtomMut(Cursor, WireType("i32")))
        if KeyValue in KeySet:
            raise ValueError("Duplicate Fusion recipe UV-order key")
        KeySet.add(KeyValue)
        Order = UvOrder(*(int(ReadAtomMut(Cursor, WireType("i32"))) for _ in range(7)))
        Entries.append(UvOrderEntry(KeyValue, Order))
    return tuple(Entries)
