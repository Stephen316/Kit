from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Tags.CheckSketchTag import CheckSketchTag
from convert.Formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields
from convert.Formats.Fusion.EntityCodec.Values.ReadFieldsMut import ReadFieldsMut
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the sketch operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadSketchMut(
    Cursor: MetaCursor, Catalog: EntityCatalog, Depth: int, Reader: KReadValue
) -> ValueStruct[KEntityValue]:
    Value = ValueStruct(ReadFieldsMut(Cursor, KSketchFields, Catalog, Depth, Reader))
    CheckSketchTag(Value)
    return Value
