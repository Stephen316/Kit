from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitFieldsMut(
    Values: tuple[NamedValue[KEntityValue], ...],
    Fields: tuple[FieldSpec[WireType], ...],
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    Selected = tuple(Field for Field in Fields if Field.IsSaved)
    Indexed = {Value.FieldName: Value.Value for Value in Values}
    if len(Indexed) != len(Values) or set(Indexed) != {
        Field.FieldName for Field in Selected
    }:
        raise ValueError("Fusion entity fields do not match the declared schema")
    Output = FeatureSink()
    for Field in Selected:
        Output.AddBytes(
            Writer(Indexed[Field.FieldName], Field.ValueType, Catalog, Depth + 1)
        )
    return bytes(Output.Buffer)
