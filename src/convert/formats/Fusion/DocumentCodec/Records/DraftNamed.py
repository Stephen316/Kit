from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadSeries,
    ReadString,
)
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def DraftNamed(Author: AuthorState, Entry: dict[str, object]) -> NamedMetadata:
    FieldName = ReadString(Entry["name"])
    TypeName = ReadString(Entry["metatype"])
    if "roles" in Entry:
        Targets = tuple(
            LocalRef(Author.Roles[ReadString(RoleName)])
            for RoleName in ReadSeries(Entry["roles"])
        )
        return NamedMetadata(
            FieldName, TypeName, ValueSeries(Targets), ReadString(Entry["element"])
        )
    if "role" in Entry:
        Target = LocalRef(Author.Roles[ReadString(Entry["role"])])
        return NamedMetadata(FieldName, TypeName, Target)
    Value = Entry["value"]
    if isinstance(Value, float):
        return NamedMetadata(FieldName, TypeName, Value)
    return NamedMetadata(FieldName, TypeName, ReadInteger(Value))
