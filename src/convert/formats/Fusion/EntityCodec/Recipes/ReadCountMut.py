from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadCountMut(Cursor: MetaCursor, Catalog: EntityCatalog) -> int:
    Count = int(ReadAtomMut(Cursor, WireType("i32")))
    if not 0 <= Count <= KMaxCount:
        raise ValueError("Fusion recipe count exceeds the supported range")
    Catalog.Quota.TakeMany(Count)
    return Count
