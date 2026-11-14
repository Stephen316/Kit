from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import ReadObject
from convert.formats.Fusion.DocumentCodec.Values.ValueConverter import KValueConverter
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


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
