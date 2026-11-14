from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KRepoRoot,
)

KVocabularies = (
    "src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json",
    "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary/FeatureClasses.json",
    "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary/PasteClasses.json",
)


def ClassGuids() -> dict[str, str]:
    return {
        Schema.NameValue: Schema.Value.ClassGuid.upper()
        for Source in KVocabularies
        for Schema in ReadVocabulary(KRepoRoot / Source)
    }


def PartRecords(
    Model: DocumentModel, ClassName: str
) -> tuple[dict[str, KEntityValue], ...]:
    Identity = ClassGuids()[ClassName]
    return tuple(
        {
            FieldValue.FieldName: FieldValue.Value
            for Group in Record.Groups
            for FieldValue in Group.Fields
        }
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.Groups[0].ClassGuid.upper() == Identity
    )
