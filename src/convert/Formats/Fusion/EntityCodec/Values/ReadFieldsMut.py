from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the fields operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadFieldsMut(
    Cursor: MetaCursor,
    Fields: tuple[FieldSpec[WireType], ...],
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> tuple[NamedValue[KEntityValue], ...]:
    return tuple(
        NamedValue(Field.FieldName, Reader(Cursor, Field.ValueType, Catalog, Depth + 1))
        for Field in Fields
        if Field.IsSaved
    )
