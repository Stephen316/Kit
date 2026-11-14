from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitGeArrayMut(
    Value: KEntityValue,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    if not isinstance(Value, GeometryArray):
        raise ValueError("Fusion geometry array requires a typed array value")
    if (
        any(
            type(Number) is not int or not 0 <= Number <= KMaxCount
            for Number in (Value.PhysicalLength, Value.GrowLength)
        )
        or len(Value.Values) > Value.PhysicalLength
    ):
        raise ValueError("Invalid Fusion geometry array allocation lengths")
    Output = FeatureSink()
    Output.AddCount(Value.Values, KMaxCount)
    Output.AddWord(Value.PhysicalLength)
    Output.AddWord(Value.GrowLength)
    for Entry in Value.Values:
        Output.AddBytes(Writer(Entry, Shape.Arguments[0], Catalog, Depth + 1))
    return bytes(Output.Buffer)
