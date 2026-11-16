from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the pairs operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
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
