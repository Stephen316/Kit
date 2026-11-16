from convert.Formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.Formats.Fusion.DocumentCodec.Values.ValueConverter import KValueConverter
from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# the convert groups contract needs a shared interpretation so model state retains its native feature and ownership relationships
def ConvertGroups(
    Value: object, Catalog: dict[str, NativeSchema], Converter: KValueConverter
) -> tuple[EntityGroup[KEntityValue], ...]:
    Groups: list[EntityGroup[KEntityValue]] = []
    for Entry in ReadSeries(Value):
        Fields = ReadObject(Entry)
        ClassGuid = ReadString(Fields["identifier"])
        Schema = Catalog[ClassGuid.upper()].Value
        Groups.append(
            EntityGroup(
                ClassGuid,
                ConvertFields(Fields["fields"], Schema.Members, Catalog, Converter),
            )
        )
    return tuple(Groups)
