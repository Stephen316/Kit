from copy import deepcopy as CopyValue

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Values.ConvertFields import ConvertFields
from convert.formats.Fusion.DocumentCodec.Values.ConvertValue import ConvertValue
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


def CheckFilled(
    ClassName: str, Members: tuple[FieldSpec[WireType], ...], Fields: dict[str, object]
) -> None:
    Missing = sorted(
        Member.FieldName
        for Member in Members
        if Member.IsSaved and Member.FieldName not in Fields
    )
    if Missing:
        raise ValueError(
            "Authored " + ClassName + " lacks required fields: " + ", ".join(Missing)
        )


def DraftGroups(
    Author: AuthorState, Entity: DraftEntity
) -> tuple[EntityGroup[KEntityValue], ...]:
    Lineage = Author.Lineage(Author.ByName[Entity.ClassName].Value.ClassGuid)
    KnownFields = {
        Member.FieldName
        for Schema in Lineage
        for Member in Schema.Value.Members
        if Member.IsSaved
    }
    if set(Entity.FieldValues) - KnownFields:
        raise ValueError("Unknown authored entity fields")
    Groups: list[EntityGroup[KEntityValue]] = []
    for Schema in Lineage:
        Fields = CopyValue(Author.Defaults.get(Schema.NameValue, {}))
        for Member in Schema.Value.Members:
            if not Member.IsSaved:
                continue
            FieldName = Member.FieldName
            if FieldName in Entity.FieldValues:
                Fields[FieldName] = Entity.FieldValues[FieldName]
            elif FieldName == "rParent":
                Fields[FieldName] = Author.Reference(Entity.ParentRole)
            elif FieldName == "children":
                Fields[FieldName] = [
                    Author.Reference(Child.RoleName)
                    for Child in Author.Entities
                    if Child.ParentRole == Entity.RoleName
                ]
        CheckFilled(Entity.ClassName, Schema.Value.Members, Fields)
        Groups.append(
            EntityGroup(
                Schema.Value.ClassGuid,
                ConvertFields(
                    Fields, Schema.Value.Members, Author.ByGuid, ConvertValue
                ),
            )
        )
    return tuple(Groups)
