from pathlib import Path as FilePath

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def NamedGroups(
    Value: DocumentModel, ClassName: str
) -> tuple[dict[str, KEntityValue], ...]:
    Source = FilePath(
        "src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json"
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
