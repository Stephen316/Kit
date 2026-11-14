from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def DimensionRows(Model: DocumentModel, ClassName: str) -> tuple[EntityRecord, ...]:
    ClassGuid = next(
        Schema.Value.ClassGuid.upper()
        for Schema in AuthorSchemas("cuboid", True)
        if Schema.NameValue == ClassName
    )
    return tuple(
        Record
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if any(Group.ClassGuid.upper() == ClassGuid for Group in Record.Groups)
    )


def DimensionFields(Record: EntityRecord) -> dict[str, KEntityValue]:
    return {
        Field.FieldName: Field.Value
        for Group in Record.Groups
        for Field in Group.Fields
    }
