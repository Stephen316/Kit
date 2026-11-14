from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


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
