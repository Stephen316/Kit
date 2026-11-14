from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def AlterMeshField(
    Record: EntityRecord, NameValue: str, Value: KEntityValue
) -> EntityRecord:
    Count = sum(
        Field.FieldName == NameValue
        for Group in Record.Groups
        for Field in Group.Fields
    )
    assert Count == 1
    Groups = tuple(
        ReplaceValue(
            Group,
            Fields=tuple(
                (
                    ReplaceValue(Field, Value=Value)
                    if Field.FieldName == NameValue
                    else Field
                )
                for Field in Group.Fields
            ),
        )
        for Group in Record.Groups
    )
    return ReplaceValue(Record, Groups=Groups)
