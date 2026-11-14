from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Tags.CheckSketchTag import CheckSketchTag
from convert.formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields
from convert.formats.Fusion.EntityCodec.Values.EmitFieldsMut import EmitFieldsMut
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue


def EmitSketchMut(
    Value: KEntityValue, Catalog: EntityCatalog, Depth: int, Writer: KEmitValue
) -> bytes:
    if not isinstance(Value, ValueStruct):
        raise ValueError("Fusion sketch tag requires named semantic fields")
    CheckSketchTag(Value)
    return EmitFieldsMut(Value.Fields, KSketchFields, Catalog, Depth, Writer)
