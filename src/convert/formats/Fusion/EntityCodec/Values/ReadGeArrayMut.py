from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadGeArrayMut(
    Cursor: MetaCursor,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> GeometryArray[KEntityValue]:
    Count = Cursor.ReadCount(KMaxCount)
    Capacity = Cursor.ReadCount(KMaxCount)
    Growth = Cursor.ReadCount(KMaxCount)
    if Count > Capacity:
        raise ValueError("Fusion geometry array count exceeds physical length")
    Values = tuple(
        Reader(Cursor, Shape.Arguments[0], Catalog, Depth + 1) for _ in range(Count)
    )
    return GeometryArray(Capacity, Growth, Values)
