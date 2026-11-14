from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitSeriesMut(
    Value: KEntityValue,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    if not isinstance(Value, ValueSeries) or len(Value.Items) > KMaxCount:
        raise ValueError("Invalid Fusion entity sequence value")
    if Shape.KindValue == "fixed" and len(Value.Items) != Shape.FixedCount:
        raise ValueError("Fusion entity fixed sequence has the wrong length")
    if Shape.KindValue == "set" and len(set(Value.Items)) != len(Value.Items):
        raise ValueError("Duplicate Fusion entity set value")
    Output = FeatureSink()
    if Shape.KindValue != "fixed":
        Output.AddCount(Value.Items, KMaxCount)
    for Entry in Value.Items:
        Output.AddBytes(Writer(Entry, Shape.Arguments[0], Catalog, Depth + 1))
    return bytes(Output.Buffer)
