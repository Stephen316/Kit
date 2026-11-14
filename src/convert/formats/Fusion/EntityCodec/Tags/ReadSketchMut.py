from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Tags.CheckSketchTag import CheckSketchTag
from convert.formats.Fusion.EntityCodec.Tags.SketchFields import KSketchFields
from convert.formats.Fusion.EntityCodec.Values.ReadFieldsMut import ReadFieldsMut
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadSketchMut(
    Cursor: MetaCursor, Catalog: EntityCatalog, Depth: int, Reader: KReadValue
) -> ValueStruct[KEntityValue]:
    Value = ValueStruct(ReadFieldsMut(Cursor, KSketchFields, Catalog, Depth, Reader))
    CheckSketchTag(Value)
    return Value
