from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitPairsMut(
    Value: KEntityValue,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    Pairs: tuple[ValuePair[KEntityValue], ...]
    if Shape.KindValue == "pair" and isinstance(Value, ValuePair):
        Pairs = (Value,)
    elif Shape.KindValue == "map" and isinstance(Value, ValueMap):
        Pairs = Value.Entries
        if len({Entry.First for Entry in Pairs}) != len(Pairs):
            raise ValueError("Duplicate Fusion entity map key")
    else:
        raise ValueError("Fusion entity value does not match pair/map declaration")
    if len(Pairs) > KMaxCount:
        raise ValueError("Fusion entity map exceeds the count limit")
    Output = FeatureSink()
    if Shape.KindValue == "map":
        Output.AddCount(Pairs, KMaxCount)
    for Entry in Pairs:
        Output.AddBytes(Writer(Entry.First, Shape.Arguments[0], Catalog, Depth + 1))
        Output.AddBytes(Writer(Entry.Second, Shape.Arguments[1], Catalog, Depth + 1))
    return bytes(Output.Buffer)
