from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def GroupFields(
    Groups: tuple[EntityGroup[KEntityValue], ...],
) -> dict[str, KEntityValue]:
    return {Field.FieldName: Field.Value for Group in Groups for Field in Group.Fields}
