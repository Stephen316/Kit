from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder
from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry
from convert.formats.Fusion.EntityCodec.Recipes.ReadCountMut import ReadCountMut
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


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
