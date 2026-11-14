from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def RectFields(
    Model: DocumentModel, ClassName: str
) -> tuple[dict[str, KEntityValue], ...]:
    Identity = next(
        Schema.Value.ClassGuid.upper()
        for Schema in AuthorSchemas("cuboid")
        if Schema.NameValue == ClassName
    )
    return tuple(
        {Field.FieldName: Field.Value for Field in Group.Fields}
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        for Group in Record.Groups
        if Group.ClassGuid.upper() == Identity
    )
