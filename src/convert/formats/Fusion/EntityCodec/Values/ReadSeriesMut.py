from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadSeriesMut(
    Cursor: MetaCursor,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> ValueSeries[KEntityValue]:
    Count = (
        Shape.FixedCount if Shape.KindValue == "fixed" else Cursor.ReadCount(KMaxCount)
    )
    Items = tuple(
        Reader(Cursor, Shape.Arguments[0], Catalog, Depth + 1) for _ in range(Count)
    )
    if Shape.KindValue == "set" and len(set(Items)) != len(Items):
        raise ValueError("Duplicate Fusion entity set value")
    return ValueSeries(Items)
