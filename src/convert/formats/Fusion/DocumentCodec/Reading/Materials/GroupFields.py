from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# the group fields contract needs a stable decomposition so model state retains its native feature and ownership relationships
def GroupFields(
    Groups: tuple[EntityGroup[KEntityValue], ...],
) -> dict[str, KEntityValue]:
    return {Field.FieldName: Field.Value for Group in Groups for Field in Group.Fields}
