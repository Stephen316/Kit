from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields
from convert.formats.Fusion.MaterialCodec.Values.DecodeLinks import DecodeLinks
from convert.formats.Fusion.MaterialCodec.Values.DecodeValue import DecodeValue
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


def DecodeFields(
    ReaderMut: MaterialReader, Fields: tuple[PropertySpec, ...], IsDefinition: bool
) -> tuple[PropertyValue, ...]:
    Values: list[PropertyValue] = []
    for Field in SelectFields(Fields, IsDefinition):
        Value = DecodeValue(ReaderMut, Field)
        Links = DecodeLinks(ReaderMut, Field.ConnectMode)
        Values.append(PropertyValue(Field.FieldName, Value, Links))
    ReaderMut.RequireEnd()
    return tuple(Values)
