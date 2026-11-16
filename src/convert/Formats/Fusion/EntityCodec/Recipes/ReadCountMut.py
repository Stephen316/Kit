from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the count operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadCountMut(Cursor: MetaCursor, Catalog: EntityCatalog) -> int:
    Count = int(ReadAtomMut(Cursor, WireType("i32")))
    if not 0 <= Count <= KMaxCount:
        raise ValueError("Fusion recipe count exceeds the supported range")
    Catalog.Quota.TakeMany(Count)
    return Count
