from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the pairs operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadPairsMut(
    Cursor: MetaCursor,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> ValuePair[KEntityValue] | ValueMap[KEntityValue]:
    Count = 1 if Shape.KindValue == "pair" else Cursor.ReadCount(KMaxCount)
    Pairs = tuple(
        ValuePair(
            Reader(Cursor, Shape.Arguments[0], Catalog, Depth + 1),
            Reader(Cursor, Shape.Arguments[1], Catalog, Depth + 1),
        )
        for _ in range(Count)
    )
    if Shape.KindValue == "pair":
        return Pairs[0]
    if len({Entry.First for Entry in Pairs}) != len(Pairs):
        raise ValueError("Duplicate Fusion entity map key")
    return ValueMap(Pairs)
