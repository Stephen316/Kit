from convert.formats.Fusion.MaterialCodec.Limits import KMaxStream
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Schema.SelectFields import SelectFields
from convert.formats.Fusion.MaterialCodec.Values.EncodeLinks import EncodeLinks
from convert.formats.Fusion.MaterialCodec.Values.EncodeValue import EncodeValue


def EncodeFields(
    Fields: tuple[PropertySpec, ...],
    Values: tuple[PropertyValue, ...],
    IsDefinition: bool,
) -> bytes:
    Selected = SelectFields(Fields, IsDefinition)
    Indexed = {Entry.FieldName: Entry for Entry in Values}
    if len(Indexed) != len(Values) or set(Indexed) != {
        Field.FieldName for Field in Selected
    }:
        raise ValueError(
            "Fusion material values do not match the declared schema group"
        )
    Payload = bytearray()
    for Field in Selected:
        Entry = Indexed[Field.FieldName]
        Payload.extend(EncodeValue(Entry.Value, Field))
        Payload.extend(EncodeLinks(Entry.Connections, Field.ConnectMode))
        if len(Payload) > KMaxStream:
            raise ValueError("Fusion material property group exceeds the size limit")
    return bytes(Payload)
