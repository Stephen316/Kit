from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def MaterialFields(Value: KEntityValue) -> dict[str, KEntityValue]:
    assert isinstance(Value, ValueObject)
    return {
        Field.FieldName: Field.Value for Group in Value.Groups for Field in Group.Fields
    }
