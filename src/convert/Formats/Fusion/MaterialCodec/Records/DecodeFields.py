from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields
from convert.Formats.Fusion.MaterialCodec.Values.DecodeLinks import DecodeLinks
from convert.Formats.Fusion.MaterialCodec.Values.DecodeValue import DecodeValue
from convert.Formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


# the fields operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
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
