from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def FindEntityField(
    Records: tuple[EntityRecord, ...], Identity: int, FieldName: str
) -> KEntityValue:
    return next(
        Field.Value
        for Entry in Records
        if Entry.ObjectId == Identity
        for Group in Entry.Groups
        for Field in Group.Fields
        if Field.FieldName == FieldName
    )
