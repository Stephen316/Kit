from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.Formats.Fusion.DocumentCodec.Values.ValueConverter import KValueConverter
from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType


# convert fields needs an explicit validity boundary so model state retains its native feature and ownership relationships
def ConvertFields(
    Value: object,
    Members: tuple[FieldSpec[WireType], ...],
    Catalog: dict[str, NativeSchema],
    Converter: KValueConverter,
) -> tuple[NamedValue[KEntityValue], ...]:
    Fields = ReadObject(Value)
    Saved = tuple(Member for Member in Members if Member.IsSaved)
    if set(Fields) != {Member.FieldName for Member in Saved}:
        raise ValueError("Authored fields differ from the declared schema")
    return tuple(
        NamedValue(
            Member.FieldName,
            Converter(Fields[Member.FieldName], Member.ValueType, Catalog),
        )
        for Member in Saved
    )
