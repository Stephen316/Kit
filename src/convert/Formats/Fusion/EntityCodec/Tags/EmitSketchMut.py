from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Tags.CheckSketchTag import CheckSketchTag
from convert.Formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields
from convert.Formats.Fusion.EntityCodec.Values.EmitFieldsMut import EmitFieldsMut
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue


# the sketch operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitSketchMut(
    Value: KEntityValue, Catalog: EntityCatalog, Depth: int, Writer: KEmitValue
) -> bytes:
    if not isinstance(Value, ValueStruct):
        raise ValueError("Fusion sketch tag requires named semantic fields")
    CheckSketchTag(Value)
    return EmitFieldsMut(Value.Fields, KSketchFields, Catalog, Depth, Writer)
