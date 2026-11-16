from pathlib import Path as FilePath

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# shared named groups setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def NamedGroups(
    Value: DocumentModel, ClassName: str
) -> tuple[dict[str, KEntityValue], ...]:
    Source = FilePath(
        "src/convert/Formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json"
    )
    Identity = next(
        Schema.Value.ClassGuid
        for Schema in ReadVocabulary(Source)
        if Schema.NameValue == ClassName
    )
    return tuple(
        {FieldValue.FieldName: FieldValue.Value for FieldValue in Group.Fields}
        for Segment in Value.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        for Group in Record.Groups
        if Group.ClassGuid == Identity
    )
