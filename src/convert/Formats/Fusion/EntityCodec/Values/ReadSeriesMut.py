from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the series operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
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
