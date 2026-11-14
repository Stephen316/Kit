from convert.formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadObject,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.DocumentCodec.Values.ValueConverter import KValueConverter
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


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
