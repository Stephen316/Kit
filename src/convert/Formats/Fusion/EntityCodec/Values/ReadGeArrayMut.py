from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the ge array operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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
