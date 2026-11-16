from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# shared find entity field setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
